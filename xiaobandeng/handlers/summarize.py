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
import traceback
from os.path import splitext
from urlparse import urlparse

import tornado.httpclient
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.escape
from concurrent.futures import ThreadPoolExecutor
from tornado.concurrent import run_on_executor

from xiaobandeng.lean_cloud import lean_cloud
from xiaobandeng.task.task import TaskGroup
from xiaobandeng.summarize.boson import BosonNLPService
from xiaobandeng.transcribe.log import TranscriptionLog
from ..task.task import increase_pending_task
from .base import BaseHandler
from .error_code import ECODE


def get_ext(url):
    """Return the filename extension from url, or ""."""
    parsed = urlparse(url)
    root, ext = splitext(parsed.path)
    return ext  # or ext[1:] if you don"t want the leading "."


class SummarizeHandler(BaseHandler):
    executor = ThreadPoolExecutor(5)

    def summarization_callback(self, task_group):
        self.summary = ''
        for task in task_group.tasks:
            logging.info(
                u"summarization result of %s : %s" %
                (task.order, task.result))
            self.summary = (task.result[0] if len(task.result) > 0 else "").encode('utf-8')


        if self.is_async:
            # if self.client_callback_url:
            #     self.notify_client(self.response_data())
            # else:
            #     self.log_content["notified_client"] = False
            #     self.save_log(True)
            pass
        else:
            self.write(json.dumps(self.response_data(), ensure_ascii=False, encoding="utf-8"))
            # self.log_content["notified_client"] = False
            # self.log_content["request_end_timestamp"] = time.time()
            # self.save_log(True)

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
        data = {
            "data": {
                "summary": "%s" % self.summary,
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


    def handle_error(self, error_code, error_message):
        self.log_content["request_end_time"] = time.time()
        self.log_content["error_type"] = str(error_code)
        self.save_log(False)

        if self.is_async:
            self.notify_client(self.response_error(error_code, error_message))
        else:
            self.write(
                json.dumps(self.response_error(error_code, error_message)))
            self.finish()

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

    @tornado.web.asynchronous
    def post(self):
        env = os.environ.get("PIPELINE_SERVICE_ENV")
        self.is_prod = (env == "production")

        have_user, error = self.check_appinfo()

        # Login failed
        if not have_user:
            self.write(json.dumps(error))
            self.finish()
            return

        # On production, we limit dev options only to admin and editor
        self.is_superuser = (not self.is_prod) or (
            self.user_mgr.is_admin() or self.user_mgr.is_editor())

        data_json = tornado.escape.json_decode(self.request.body)

        self.content = data_json.get("content", "")
        self.title = data_json.get("title", "")

        is_async = self.get_argument("async", True)
        if is_async == "false" or is_async == "False":
            is_async = False
        else:
            is_async = True
        self.is_async = is_async

        self.client_callback_url = self.get_argument("callback_url", None)
        if self.is_async and (not self.client_callback_url):
            self.write(json.dumps(self.error_missing_arg("callback_url")))
            self.finish()
            return

        if self.is_async:
            tornado.ioloop.IOLoop.current().add_callback(
                self._handle, self.content
            )
            self.write(
                json.dumps(self.response_success(
                    {"data": {"summary": self.summary}}), ensure_ascii=False, encoding="utf-8"))
            self.finish()
            return
        else:
            self._handle(self.title, self.content)

    def _handle(self, title, content):
        # create a task group to organize transcription tasks
        task_group = TaskGroup(self.summarization_callback)

        try:
            boson_service = BosonNLPService()
            boson_tasks = boson_service.batch_summarization_tasks([title], [content])
            self.enqueue_tasks(task_group, boson_tasks)
        except Exception:
            logging.exception('exception caught using Boson')
            traceback.print_exc()

        task_group.start()
