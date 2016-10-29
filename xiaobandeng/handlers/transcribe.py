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
import traceback
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
from ..task.task import increase_pending_task
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
                self.notify_client(self.response_data())
            else:
                self.log_content["notified_client"] = False
                self.save_log(True)
        else:
            self.write(json.dumps(self.response_data()))
            self.log_content["notified_client"] = False
            self.log_content["request_end_timestamp"] = time.time()
            self.save_log(True)
            self.finish()

    def save_log(self, status):
        self.log_content["transcribe_end_timestamp"] = time.time()
        self.log_content["media_id"] = self.media_id
        self.log_content["status"] = "success" if status else "failure"
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

    def notify_client(self, resp):
        def notified_callback(response):
            logging.info("called origin client server...")
            self.log_content["notified_client"] = True

            if response.error:
                self.save_log(False)
                logging.info("origin client server returned error.")
            else:
                self.save_log(True)
                logging.info("origin client server returned success")

        logging.info("notify callback : %s" % str(resp))
        client = tornado.httpclient.AsyncHTTPClient()
        client.fetch(self.client_callback_url,
                     callback=notified_callback,
                     method="POST",
                     body=urllib.urlencode(resp))


    def on_donwload(self, tmp_file, ext, language, response):
        if response.error:
            self.log_content["request_end_time"] = time.time()
            self.log_content["error_type"] = "download_addr"
            self.save_log(False)

            error_code = 1003
            error_msg = "Media download error. Check your media address."
            if self.is_async:
                self.notify_client(self.response_error(error_code, error_msg))
            else:
                self.write(
                    json.dumps(self.response_error(error_code, error_msg)))
                self.finish()
            return

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
            self.requirement,
            language.split(","),
            self.service_providers,
        )

        vad_aggressiveness = 0

        audio_dir, starts, is_voices, break_pause = vad.slice(vad_aggressiveness, target_file)

        starts, durations = preprocessor.preprocess_clip_length(
            audio_dir,
            starts,
            is_voices,
            break_pause,
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
            try:
                lan = language
                if self.is_prod:
                    if "zh" in language.split(","):
                        lan = "zh"
                    else:
                        raise Exception
                baidu_speech_service = baidu.BaiduNLP()
                baidu_tasks = baidu_speech_service.batch_vop_tasks(
                    file_list, starts, durations, lan)
                self.enqueue_tasks(task_group, baidu_tasks)
            except Exception:
                pass

        if "google" in self.service_providers:
            try:
                lan = language
                if self.is_prod:
                    if "en" in language.split(","):
                        lan = "en"
                    else:
                        raise Exception
                google_speech_service = google.GoogleASR()
                google_tasks = google_speech_service.batch_vop_tasks(
                    file_list, starts, durations, lan)
                self.enqueue_tasks(task_group, google_tasks)
            except Exception:
                traceback.print_exc()
                print '---'*200
                pass

        # you need to smoothen the file after building all tasks but
        # before task group starts
        # preprocessor.smoothen_clips_edge(file_list)
        task_group.start()

    def enqueue_tasks(self, task_group, tasks):
        for task in tasks:
            increase_pending_task(1)
            task_group.add(task)

    def error_missing_arg(self, arg_name):
        return self.response_error(1002, "parameter is missing: %s" % arg_name)

    def error_invalid_arg(self, arg_name):
        return self.response_error(1002,
                                   "parameter has invalid value %s" % arg_name)

    @tornado.web.asynchronous
    def get(self):
        env = os.environ.get("PIPELINE_SERVICE_ENV")
        self.is_prod = (env == "production")

        company_login_state, error = self.check_company_user()
        if not company_login_state:
            self.write(json.dumps(error))
            self.finish()
            return
        addr = self.get_argument("addr", None)
        if addr == None:
            self.write(json.dumps(self.error_missing_arg("addr")))
            self.finish()
        addr = urllib.quote(addr.encode("utf8"), ":/")
        self.addr = addr

        media_name = self.get_argument("media_name", None)
        if media_name == None:
            self.write(json.dumps(self.error_missing_arg("media_name")))
            self.finish()

        self.media_name = media_name.encode("utf8")
        self.media_id = str(uuid.uuid4())
        self.language = self.get_argument("lan", "zh")

        self.company_name = None
        if not self.is_prod:
            self.company_name = self.get_argument("company", None)

        if self.company_name == None:
            current_user = self.user_mgr.current_user()
            self.company_name = current_user.get("company_name")

        self.company_name = self.company_name.encode("utf8")

        if not self.is_prod:
            fragment_length_limit = self.get_argument("max_fragment_length", 10)
            if fragment_length_limit:
                fragment_length_limit = int(fragment_length_limit)
            self.fragment_length_limit = fragment_length_limit
        else:
            self.fragment_length_limit = 10

        if not self.is_prod:
            self.requirement = self.get_argument("requirement",
                                                 u"字幕,纯文本,关键词,摘要").split(",")
        else:
            self.requirement = []

        if not self.is_prod:
            upload_oss = self.get_argument("upload_oss", False)
            if upload_oss == "true" or upload_oss == "True":
                self.upload_oss = True
            else:
                self.upload_oss = False
        else:
            self.upload_oss = False

        if not self.is_prod:
            self.service_providers = self.get_argument(
                "service_providers", "baidu").split(",")
        else:
            lans = self.language.split(",")
            if len(lans) > 1:
                self.service_providers = ["baidu","google"]
            elif "en" in lans:
                self.service_providers = ["google"]
            else:
                self.service_providers = ["baidu"]

        self.client_callback_url = self.get_argument("callback_url", None)

        if not self.is_prod:
            force_fragment_length = self.get_argument("force_fragment_length",
                                                      False)
            if force_fragment_length == "true" or force_fragment_length == "True":
                force_fragment_length = True
            else:
                force_fragment_length = False
            self.force_fragment_length = force_fragment_length
        else:
            self.force_fragment_length = False

        if not self.is_prod:
            is_async = self.get_argument("async", True)
            if is_async == "false" or is_async == "False":
                is_async = False
            else:
                is_async = True
            self.is_async = is_async
        else:
            self.is_async = True

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
            tornado.ioloop.IOLoop.current().add_callback(
                self._handle, self.addr, self.language
            )
            self.write(json.dumps(self.response_success()))
            self.log_content["request_end_time"] = time.time()
            self.finish()
        else:
            self._handle(self.addr, self.language)

    def _handle(self, addr, language):
        ext = get_ext(addr)
        tmp_file = tempfile.NamedTemporaryFile(suffix=ext).name
        client = tornado.httpclient.AsyncHTTPClient(
            max_body_size=1024 * 1024 * 1024 * 0.8)
        # call self.ondownload after get the request file
        logging.info("downloading: %s" % addr)
        client.fetch(addr,
                     callback=functools.partial(self.on_donwload,
                                                tmp_file, ext, language),
                     connect_timeout=120,
                     request_timeout=600, )
