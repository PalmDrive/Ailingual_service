# -*- coding: utf-8 -*-

from __future__ import absolute_import

import functools
import json
import logging
import os
import tempfile
import time
import urllib
import uuid
import wave
from os.path import splitext
from urlparse import urlparse

import tornado.httpclient
import tornado.httpserver
import tornado.ioloop
import tornado.web
from concurrent.futures import ThreadPoolExecutor
from tornado.concurrent import run_on_executor

from xiaobandeng.ali_cloud import oss
from xiaobandeng.lean_cloud import lean_cloud
from xiaobandeng.medium import convertor
from xiaobandeng.medium import preprocessor
from xiaobandeng.medium import vad
from xiaobandeng.task.task import TaskGroup
from xiaobandeng.transcribe import baidu
from xiaobandeng.transcribe import google
from xiaobandeng.transcribe.log import TranscriptionLog
from ..task.task  import increase_pending_task
from .base import BaseHandler


def get_ext(url):
    """Return the filename extension from url, or ""."""
    parsed = urlparse(url)
    root, ext = splitext(parsed.path)
    return ext  # or ext[1:] if you don"t want the leading "."


class TranscribeHandler(BaseHandler):
    executor = ThreadPoolExecutor(5)

    @run_on_executor
    def upload_oss_in_thread(self, media_id, file_list):
        # since oss api uses requests lib,the socket can not be
        # selected by epoll
        # now use a thread to make it run concurrently.
        # but
        oss.upload(media_id, file_list)
        logging.info("-----upload oss over-------")

    def write_file(self, response, file_name):
        f = open(file_name, "wb")
        f.write(response.body)
        f.close()
        logging.info("write file:%s" % file_name)

    def transcription_callback(self, task_group):
        # warn: this method will change task.result
        # punc_task_group(task_group)

        for task in task_group.tasks:
            # for play
            end_at = task.start_time + task.duration - 0.01
            task.start_time += 0.01

            results = task.result
            logging.info(
                u"transcript result of %s : %s, duration %f, end_at %f" %
                (task.file_name, task.result, task.duration, end_at))
            fragment_src = oss.media_fragment_url(
                self.media_id, task.file_name
            )
            self.cloud_db.set_fragment(
                task.order,
                task.start_time,
                end_at,
                self.media_id,
                fragment_src)
            for result in results:
                self.cloud_db.add_transcription_to_fragment(
                    task.order, result, task.source_name())

        self.cloud_db.save()
        if self.upload_oss:
            self.cloud_db.create_crowdsourcing_tasks()

        if self.is_async:
            if self.client_callback_url:
                self.notify_client()
            else:
                self.log_content['notified_client'] = False
                self.save_log(True)
        else:
            self.write(json.dumps(self.response_data()))
            self.log_content['notified_client'] = False
            self.log_content["request_end_timestamp"] = time.time()
            self.save_log(True)
            self.finish()

    def save_log(self, status):
        self.log_content["transcribe_end_timestamp"] = time.time()
        self.log_content["media_id"] = self.media_id
        self.log_content["status"] = "success" if status else "fail"
        log = TranscriptionLog()
        log.add(self.log_content)
        log.save()

    def response_data(self):
        self.download_link = "/medium/%s/srt" % self.media_id

        data = {
            "data": {
                "media_id": "%s" % self.media_id,
                "transcript_srt_download_link": "%s" % self.download_link
            }
        }

        return data

    def notify_client(self):
        def notified_callback(response):
            logging.info("called origin client server...")
            self.log_content['notified_client'] = True

            if response.error:
                self.save_log(False)
                logging.info("origin client server returned error.")
            else:
                self.save_log(True)
                logging.info("origin client server returned success")

        client = tornado.httpclient.AsyncHTTPClient()
        client.fetch(self.client_callback_url,
                     callback=notified_callback,
                     method="POST",
                     body=urllib.urlencode(self.response_data()))

    def on_donwload(self, tmp_file, ext, language, response):
        if response.error:
            self.write("media download error:%s" % str(response.code))
            self.log_content["request_end_time"] = time.time()
            self.log_content["error_type"] = 'download_addr'
            self.save_log(False)
            self.finish()

        logging.info("downloaded,saved to: %s" % tmp_file)
        self.write_file(response, tmp_file)

        target_file = convertor.convert_to_wav(ext, tmp_file)

        wav = wave.open(target_file)
        duration = wav.getnframes() / float(wav.getframerate())
        wav.close()
        self.log_content["media_duration"] = duration

        self.cloud_db = lean_cloud.LeanCloud()
        self.cloud_db.add_media(
            self.media_name,
            self.media_id,
            self.addr,
            duration,
            self.company_name,
            self.requirement)

        audio_dir, starts = vad.slice(3, target_file)
        starts = preprocessor.preprocess_clip_length(
            audio_dir,
            starts,
            self.fragment_length_limit,
            self.force_fragment_length)

        basedir, subdir, files = next(os.walk(audio_dir))
        file_list = [os.path.join(basedir, file) for file in sorted(files)]

        # Upload media clips to Aliyun OSS
        if self.upload_oss:
            tornado.ioloop.IOLoop.instance().add_callback(
                functools.partial(
                    self.upload_oss_in_thread, self.media_id, file_list
                ))

        # create a task group to organize transcription tasks
        task_group = TaskGroup(self.transcription_callback)

        if "baidu" in self.service_providers:
            baidu_speech_service = baidu.BaiduNLP()
            baidu_tasks = baidu_speech_service.batch_vop_tasks(
                file_list, starts, language)
            for task in baidu_tasks:
                increase_pending_task(1)
                task_group.add(task)

        if "google" in self.service_providers:
            google_speech_service = google.GoogleASR()
            google_tasks = google_speech_service.batch_vop_tasks(
                file_list, starts, language)
            for task in google_tasks:
                increase_pending_task(1)
                task_group.add(task)

        # you need to smoothen the file after building all tasks but
        # before task group starts
        preprocessor.smoothen_clips_edge(file_list)
        task_group.start()

    @tornado.web.asynchronous
    def get(self):
        addr = self.get_argument("addr")
        addr = urllib.quote(addr.encode("utf8"), ":/")

        self.addr = addr
        self.media_name = self.get_argument("media_name").encode("utf8")
        self.media_id = str(uuid.uuid4())
        self.language = self.get_argument("lan", "zh")
        self.company_name = self.get_argument("company").encode("utf8")

        fragment_length_limit = self.get_argument("max_fragment_length", 10)
        if fragment_length_limit:
            fragment_length_limit = int(fragment_length_limit)
        self.fragment_length_limit = fragment_length_limit
        self.requirement = self.get_argument("requirement",
                                             u"字幕,纯文本,关键词,摘要").split(',')

        upload_oss = self.get_argument("upload_oss", False)
        if upload_oss == "true" or upload_oss == "True":
            self.upload_oss = True
        else:
            self.upload_oss = False
        self.service_providers = self.get_argument(
            "service_providers", "baidu").split(",")

        self.client_callback_url = self.get_argument("callback", None)

        force_fragment_length = self.get_argument("force_fragment_length",
                                                  False)
        if force_fragment_length == "true" or force_fragment_length == "True":
            force_fragment_length = True
        else:
            force_fragment_length = False
        self.force_fragment_length = force_fragment_length

        self.is_async = self.get_argument("async", False)

        self.log_content = {}
        self.log_content["request_start_timestamp"] = time.time()
        self.log_content["arguments_get"] = self.request.arguments
        self.log_content["arguments_post"] = self.request.body_arguments
        self.log_content["ip"] = self.request.remote_ip
        self.log_content["agent"] = self.request.headers.get("User-Agent", "")
        self.log_content["path"] = self.request.path
        self.log_content["uri"] = self.request.uri
        self.log_content["method"] = self.request.method
        self.log_content["headers"] = str(self.request.headers)

        if self.is_async:
            company_login_state, error = self.check_company_user()
            if company_login_state:
                tornado.ioloop.IOLoop.current().add_callback(
                    self._handle, self.addr, self.language
                )
                self.write(json.dumps({"status": "success"}))
                self.log_content["request_end_time"] = time.time()
                self.finish()
            else:
                self.write(json.dumps({"status": "fail", "message":error }))
        else:
            self._handle(self.addr, self.language)

    def _handle(self, addr, language):
        ext = get_ext(addr)
        tmp_file = tempfile.NamedTemporaryFile().name + ext
        client = tornado.httpclient.AsyncHTTPClient(
            max_body_size=1024 * 1024 * 1024 * 0.8)
        # call self.ondownload after get the request file
        logging.info("downloading: %s" % addr)
        client.fetch(addr,
                     callback=functools.partial(self.on_donwload,
                                                tmp_file, ext, language),
                     connect_timeout=120,
                     request_timeout=600, )
