# -*- coding: utf-8 -*-

from __future__ import absolute_import

import json
import logging
import os
import time
import urllib
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

from xiaobandeng.lean_cloud import lean_cloud_summarize
from xiaobandeng.task.task import TaskGroup
from xiaobandeng.summarize.boson import BosonNLPService
from xiaobandeng.summarize.tuofeng import TuofengNLPService
from xiaobandeng.transcribe.log import TranscriptionLog
from xiaobandeng.task.task import increase_pending_task
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
            self.summary = task.result[0] if len(task.result) > 0 else ""

        self.cloud_db.set_summary(self.summary)
        self.text_analysis_id = self.cloud_db.save()

        if self.is_async:
            if self.client_callback_url:
                self.notify_client(self.response_data())
            else:
                self.log_content["notified_client"] = False
                #self.save_log(True)
        else:
            self.write(self.response_data())
            self.log_content["notified_client"] = False
            self.log_content["request_end_timestamp"] = time.time()
            # self.save_log(True)

            self.finish()
            return

    def save_log(self, status):
        # TODO: add transaction log
        # self.log_content["transcribe_end_timestamp"] = time.time()
        # self.log_content["text_analysis_id"] = self.text_analysis_id
        # self.log_content["status"] = "success" if status else "failure"
        # log = TranscriptionLog()
        # log.add(self.log_content)
        # log.save()
        pass

    def response_data(self):
        data = {
            "data": {
                "id" : self.text_analysis_id,
                "summary": "%s" % self.summary
            }
        }

        return data

    def notify_client(self, resp):
        def notified_callback(response):
            logging.info("called origin client server...")
            # self.log_content["notified_client"] = True

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
                self.response_error(error_code, error_message)
            )
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

        authenticated, error = self.authenticate()

        # Login failed
        if not authenticated:
            self.write(error)
            self.finish()
            return

        # On production, we limit dev options only to admin and editor
        self.is_superuser = (not self.is_prod) or (not self.session_manager.is_client_company())

        data_json = tornado.escape.json_decode(self.request.body)

        self.content = data_json.get("content", "")
        self.title = data_json.get("title", "")

        if self.is_superuser:
            self.service_providers = self.get_argument("service_providers", "boson").split(",")
        else:
            self.service_providers = ["boson"]

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

        self.cloud_db = lean_cloud_summarize.LeanCloudSummarize()
        self.cloud_db.init_text_analyisis(self.title, self.content, self.session_manager.company.id)
        self.text_analysis_id = self.cloud_db.save()

        if self.is_async:
            tornado.ioloop.IOLoop.current().add_callback(
                self._handle, self.title, self.content
            )
            self.write(
                self.response_success({
                    "data" : {"id" : self.text_analysis_id}
                })
            )
            self.finish()
            return
        else:
            self._handle(self.title, self.content)


    def _handle(self, title, content):
        # create a task group to organize summarization tasks
        task_group = TaskGroup(self.summarization_callback)

        if "boson" in self.service_providers:
            try:
                boson_service = BosonNLPService()
                boson_tasks = boson_service.batch_summarization_tasks([title], [content])
                self.enqueue_tasks(task_group, boson_tasks)
            except Exception:
                logging.exception('exception caught using Boson')
                traceback.print_exc()

        elif "tuofeng" in self.service_providers:
            try:
                tuofeng_service = TuofengNLPService()
                tuofeng_tasks = tuofeng_service.batch_summarization_tasks([title], [content])
                self.enqueue_tasks(task_group, tuofeng_tasks)
            except Exception:
                logging.exception('exception caught using Tuofeng')
                traceback.print_exc()

        task_group.start()
