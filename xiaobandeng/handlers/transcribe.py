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
import shutil
import tornado.httpclient
import tornado.httpserver
import tornado.ioloop
import tornado.web
from concurrent.futures import ThreadPoolExecutor

from xiaobandeng.ali_cloud import oss
from xiaobandeng.lean_cloud import lean_cloud
from xiaobandeng.medium import convertor
from xiaobandeng.medium import preprocessor
from xiaobandeng.medium import vad
from xiaobandeng.task.task import TaskGroup
from xiaobandeng.transcribe import baidu
from xiaobandeng.transcribe import google
from xiaobandeng.transcribe.log import TranscriptionLog
from xiaobandeng.task.task import increase_pending_task
from .base import BaseHandler
from .error_code import ECODE


def get_ext(url):
    """Return the filename extension from url, or ""."""
    parsed = urlparse(url)
    root, ext = splitext(parsed.path)
    return ext  # or ext[1:] if you don"t want the leading "."


class TranscribeHandler(BaseHandler):
    executor = ThreadPoolExecutor(5)

    # @run_on_executor
    # batch upload to oss, batch upload to leancloud
    # sets fragment's downloading url  if uploading oss is success
    # can not run two actions concurrently now since batch upload leancloud
    # once

    def upload_to_oss(self, media_id, task_group):
        # upload to oss and create crowdsourcing tasks
        oss.upload(media_id, task_group, self.cloud_db)

        logging.info("-----upload oss over-------")
        self.cloud_db.batch_create_crowdsourcing_tasks(task_group)
        logging.info("-----create crowdsourcing tasks over-------")

    def transcription_callback(self, task_group):
        # warn: this method will change task.result
        # punc_task_group(task_group)

        for task in task_group.tasks:
            # for play
            end_at = task.start_time + task.duration - 0.01
            task.start_time += 0.01

            results = task.result
            # logging.info(
            #     u"transcript result of %s : %s, duration %f, end_at %f" %
            #     (task.file_name, task.result, task.duration, end_at))

            # fragment_src = oss.media_fragment_url(
            # self.media_id, task.file_name
            # )
            # after uploaded to oss,fragment_src will be set
            #
            self.cloud_db.set_fragment(
                task.order,
                task.start_time,
                end_at,
                self.media_id,
                "")

            for result in results:
                self.cloud_db.add_transcription_to_fragment(
                    task.order, result, task.source_name())

        # save all fragments
        self.cloud_db.save()

        # Upload media clips to Aliyun OSS
        if self.upload_oss:
            self.upload_to_oss(self.media_id, task_group)
            self.cloud_db.batch_update_fragment_url()

        #delete media dir
        print 'deleting media clip dir...'
        shutil.rmtree(self.tmp_media_dir)


        if self.is_async:
            if self.client_callback_url:
                self.notify_client(self.response_data())
            else:
                self.log_content["notified_client"] = False
                self.save_log(True)
        else:
            self.write(self.response_data())
            self.log_content["notified_client"] = False
            self.log_content["request_end_timestamp"] = time.time()
            self.save_log(True)

            self.finish()
            return

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
            self.handle_error(*ECODE.ERR_MEDIA_DOWNLOAD_FAILURE)
            return

        logging.info("downloaded,saved to: %s" % tmp_file.name)
        tmp_file.write(response.body)
        tmp_file.flush()

        try:
            wave_file_name = convertor.convert_to_wav(tmp_file.name)

            wav = wave.open(wave_file_name, "rb")
            duration = wav.getnframes() / float(wav.getframerate())

            self.log_content["media_duration"] = duration
        except Exception:
            logging.exception(
                'exception caught in converting media type - ' + ext)
            traceback.print_exc()
            self.handle_error(*ECODE.ERR_MEDIA_UNSUPPORTED_FORMAT)
            return

        self.cloud_db = lean_cloud.LeanCloud()
        self.cloud_db.add_media(
            self.media_name,
            self.media_id,
            self.addr,
            duration,
            self.session_manager.company.id,
            self.client_id,
            self.requirement,
            language.split(","),
            self.service_providers,
            {"machine": 1},
            self.caption_type
        )

        vad_aggressiveness = 2

        audio_dir, starts, is_voices, break_pause = vad.slice(
            vad_aggressiveness, wave_file_name)

        #wave file name
        os.remove(wave_file_name)
        tmp_file.close()
        wav.close()
        print 'removed temp file.'

        starts, durations = preprocessor.preprocess_clip_length(
            audio_dir,
            starts,
            is_voices,
            break_pause,
            self.fragment_length_limit,
            self.force_fragment_length)

        basedir, subdir, files = next(os.walk(audio_dir))
        self.file_list = file_list = [os.path.join(basedir, file) for file in
                                      sorted(files)]
        self.tmp_media_dir = basedir

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
                logging.exception('exception caught using baidu ASR')
                traceback.print_exc()

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
                logging.exception('exception caught using google ASR')
                traceback.print_exc()

        # you need to smoothen the file after building all tasks but
        # before task group starts
        # preprocessor.smoothen_clips_edge(file_list)
        task_group.start()

    def enqueue_tasks(self, task_group, tasks):
        for task in tasks:
            increase_pending_task(1)
            task_group.add(task)

    def error_missing_arg(self, arg_name):
        return self.response_error(100001,
                                   "parameter is missing: %s" % arg_name)

    def error_invalid_arg(self, arg_name):
        return self.response_error(100002,
                                   "parameter has invalid value %s" % arg_name)

    def handle_error(self, error_code, error_message):
        self.log_content["request_end_time"] = time.time()
        self.log_content["error_type"] = error_code
        self.save_log(False)

        if self.is_async:
            self.notify_client(self.response_error(error_code, error_message))
        else:
            self.write(
                self.response_error(error_code, error_message)
            )
            self.finish()

    @tornado.web.asynchronous
    def get(self):
        env = os.environ.get("PIPELINE_SERVICE_ENV")
        self.is_prod = (env == "production")

        authenticated, error = self.authenticate()

        # Login failed
        if not authenticated:
            self.write(error)
            self.finish()
            return

        # On production, we limit dev options only to admin and editor
        self.is_superuser = (not self.is_prod) or (not self.session_manager.is_client_company())

        addr = self.get_argument("addr", None)
        if addr == None:
            self.write(self.error_missing_arg("addr"))
            self.finish()
            return
        addr = urllib.quote(addr.encode("utf8"), ":/")
        self.addr = addr

        self.caption_type = self.get_argument("caption_type")

        media_name = self.get_argument("media_name", None)
        if media_name == None:
            self.write(self.error_missing_arg("media_name"))
            self.finish()
            return
        self.media_name = media_name.encode("utf8")
        self.media_id = str(uuid.uuid4())
        self.language = self.get_argument("lan", "zh")

        if self.is_superuser:
            self.client_id = self.get_argument("client_id", None)
        else:
            self.client_id = None

        if not self.client_id:
            self.client_id = self.session_manager.company.id

        if self.is_superuser:
            fragment_length_limit = self.get_argument("max_fragment_length", 10)
            if fragment_length_limit:
                fragment_length_limit = int(fragment_length_limit)
            self.fragment_length_limit = fragment_length_limit
        else:
            self.fragment_length_limit = 7

        self.requirement = self.get_argument("requirement",
                                             u"字幕,纯文本,关键词,摘要").split(",")

        if self.is_superuser:
            upload_oss = self.get_argument("upload_oss", False)
            if upload_oss == "true" or upload_oss == "True":
                self.upload_oss = True
            else:
                self.upload_oss = False
        else:
            self.upload_oss = False

        if self.is_superuser:
            self.service_providers = self.get_argument(
                "service_providers", "baidu").split(",")
        else:
            lans = self.language.split(",")
            if len(lans) > 1:
                self.service_providers = ["baidu", "google"]
            elif "en" in lans:
                self.service_providers = ["google"]
            else:
                self.service_providers = ["baidu"]

        if self.is_superuser:
            force_fragment_length = self.get_argument("force_fragment_length",
                                                      False)
            if force_fragment_length == "true" or force_fragment_length == "True":
                force_fragment_length = True
            else:
                force_fragment_length = False
            self.force_fragment_length = force_fragment_length
        else:
            self.force_fragment_length = False

        is_async = self.get_argument("async", True)
        if is_async == "false" or is_async == "False":
            is_async = False
        else:
            is_async = True
        self.is_async = is_async

        self.client_callback_url = self.get_argument("callback_url", None)
        if self.is_async and (not self.client_callback_url):
            self.write(self.error_missing_arg("callback_url"))
            self.finish()
            return

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
            self.write(
                self.response_success(
                    {
                        "data": {
                        "media_id": self.media_id
                        }
                    }
                )
            )
            self.log_content["request_end_time"] = time.time()
            self.finish()
            return
        else:
            self._handle(self.addr, self.language)

    def _handle(self, addr, language):
        ext = get_ext(addr)
        # this is a temporary file ,will be removed after close()
        tmp_file = tempfile.NamedTemporaryFile("wb+", suffix=ext)
        client = tornado.httpclient.AsyncHTTPClient(
            max_body_size=1024 * 1024 * 1024 * 0.8)
        # call self.ondownload after get the request file
        logging.info("downloading: %s" % addr)
        client.fetch(addr,
                     callback=functools.partial(self.on_donwload,
                                                tmp_file, ext, language),
                     connect_timeout=120,
                     request_timeout=600, )
