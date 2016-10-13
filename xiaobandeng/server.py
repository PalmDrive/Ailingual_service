# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os
import tornado.httpclient
import tornado.ioloop
import tornado.web
import tornado.httpserver
import urllib
import tempfile
import vad
import lean_cloud
import convertor
import preprocessor
import uuid
import json
import logging
import datetime
import env_config
import time
import functools
import oss
import wave
import multiprocessing
import re

from urlparse import urlparse
from os.path import splitext
from user import UserMgr
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor
from transcribe import baidu, google
from transcribe.task import TaskGroup
from transcribe.log import TranscriptionLog


def get_ext(url):
    """Return the filename extension from url, or ""."""
    parsed = urlparse(url)
    root, ext = splitext(parsed.path)
    return ext  # or ext[1:] if you don"t want the leading "."


class BaseHandler(tornado.web.RequestHandler):
    def prepare(self):
        # set access control allow_origin
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers",
                        "X-Requested-With, Content-Type,"
                        "x-smartchat-key,client-source")
        self.set_header("Access-Control-Allow-Methods",
                        "PUT,POST,GET,DELETE,OPTIONS")
        # 如果CORS请求将withCredentials标志设置为true，使得Cookies可以随着请求发送。
        # 如果服务器端的响应中,没有返回Access-Control-Allow-Credentials: true的响应头，
        # 那么浏览器将不会把响应结果传递给发出请求的脚本程序.

        # 给一个带有withCredentials的请求发送响应的时候,
        # 服务器端必须指定允许请求的域名,不能使用"*".否则无效
        # self.set_header("Access-Control-Allow-Credentials", "true")

    def options(self):
        self.set_header("Allow", "GET,HEAD,POST,PUT,DELETE,OPTIONS")

    def check_company_user(self):
        user_mgr = UserMgr()
        app_id = self.request.headers.get("app_id", "")
        app_key = self.request.headers.get("app_key", "")
        # return (true_or_false,user)
        if app_id and app_key:
            return user_mgr.login(app_id, app_key)
        else:
            return (
                False, Exception("app_id or app_key not found in http headers"))


class TestHandler(BaseHandler):
    def get(self):
        self.write("test ok")


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

        if not self.is_async:
            self.write(json.dumps({
                "media_id": self.media_id
            }))
            self.log_content["request_end_timestamp"] = time.time()
            self.save_log(True)
            self.finish()
        elif self.client_callback_url:
            self.notified_client()

    def save_log(self, status):
        self.log_content["transcribe_end_timestamp"] = time.time()
        self.log_content["result"] = self.media_id
        self.log_content["status"] = "success" if status else "fail"
        log = TranscriptionLog()
        log.add(self.log_content)
        log.save()

    def notified_client(self):
        def notified_callback(response):
            logging.info("called origin client server...")
            self.log_content["request_end_time"] = time.time()
            self.log_content['notified_client'] = True

            if not response.error:
                self.save_log(True)
                logging.info("origin client server returned success")
            else:
                self.save_log(False)
                logging.info("origin client server returned error.")

        self.download_link = "/medium/(%s)/srt" % self.media_id

        post_data = {
            "data": {
                "media_id": "%s" % self.media_id,
                "transcript_srt_download_link": "%s" % self.download_link
            }
        }

        client = tornado.httpclient.AsyncHTTPClient()
        client.fetch(self.client_callback_url,
                     callback=notified_callback,
                     method="POST",
                     body=urllib.urlencode(post_data)
        )


    def on_donwload(self, tmp_file, ext, language, response):
        if response.error:
            self.write("media download error:%s" % str(response.code))
            self.log_content["request_end_time"] = time.time()
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

        audio_dir, starts = vad.slice(0, target_file)
        if self.fragment_length_limit:
            starts = preprocessor.preprocess_clip_length(
                audio_dir, starts, self.fragment_length_limit)
        else:
            starts = preprocessor.preprocess_clip_length(audio_dir, starts)

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
                task_group.add(task)

        num_workers = multiprocessing.cpu_count()
        pool = multiprocessing.Pool(num_workers)
        if "google" in self.service_providers:
            google_speech_servce = google.GoogleASR(pool)
            google_tasks = google_speech_servce.batch_vop_tasks(
                file_list, starts, language)
            for task in google_tasks:
                task_group.add(task)

        task_group.start()

    @tornado.web.asynchronous
    def get(self):
        addr = self.get_argument("addr")
        addr = urllib.quote(addr.encode("utf8"), ":/")

        media_name = self.get_argument("media_name").encode("utf8")
        language = self.get_argument("lan", "zh")
        company_name = self.get_argument("company").encode("utf8")
        fragment_length_limit = self.get_argument("max_fragment_length", 10)
        if fragment_length_limit:
            fragment_length_limit = int(fragment_length_limit)
        upload_oss = self.get_argument("upload_oss", False)
        requirement = self.get_argument("requirement", u"字幕/纯文本/关键词/摘要")
        if upload_oss == "true" or upload_oss == "True":
            upload_oss = True
        else:
            upload_oss = False
        service_providers = self.get_argument(
            "service_providers", "baidu").split(",")
        self.addr = addr
        self.media_name = media_name
        self.media_id = str(uuid.uuid4())
        self.language = language
        self.company_name = company_name
        self.fragment_length_limit = fragment_length_limit
        self.upload_oss = upload_oss
        self.service_providers = service_providers
        self.requirement = requirement.split(",")
        self.client_callback_url = self.get_argument("callback", None)
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
            tornado.ioloop.IOLoop.current().add_callback(
                self._handle, addr, language
            )
            self.write("success")
            self.finish()
        else:
            self._handle(addr, language)

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


class SrtHandler(BaseHandler):
    def get(self, media_id):
        source = self.get_argument("service_source", 0)

        lc_content_keys = ["content_baidu", "content_google"]
        content_key = lc_content_keys[int(source)]

        lc = lean_cloud.LeanCloud()
        media_list = lc.get_list(media_id=media_id)

        def convert_time(seconds):
            seconds = round(seconds, 3)
            t_start = datetime.datetime(1970, 1, 1)
            t_delta = datetime.timedelta(seconds=seconds)
            t_end = t_start + t_delta
            time_tuple = (t_end.hour - t_start.hour,
                          t_end.minute - t_start.minute,
                          t_end.second - t_start.second,
                          t_end.microsecond - t_start.microsecond)
            return ":".join([str(i) for i in time_tuple[:-1]]) + "," + \
                   "%d" % (time_tuple[-1] / 1000)

        if media_list:
            filename = lc.get_media(media_id).get("media_name")
            self.set_header("Content-Type", "application/octet-stream")
            self.set_header("Content-Disposition",
                            "attachment; filename=" + filename + ".srt")
            for (index, media) in enumerate(media_list, 1):
                self.write(str(media.get("fragment_order") + 1))
                self.write("\n")
                self.write(
                    convert_time(media.get("start_at")) + "	-->	" +
                    convert_time(media.get("end_at")))
                self.write("\n")

                content_list = media.get(content_key)

                content = content_list[0] if content_list else ""
                content = re.sub(u"[,，。\.?？!！]", " ", content)
                self.write(content)
                self.write("\n")
                self.write("\n")
            self.finish()

        else:
            self.write("not exist")


class LrcHandler(BaseHandler):

    def get(self, media_id):
        source = self.get_argument("service_source", 0)

        lc_content_keys = ["content_baidu", "content_google"]
        self.content_key = lc_content_keys[int(source)]

        lc = lean_cloud.LeanCloud()
        media_list = lc.get_list(media_id=media_id)
        if media_list:
            filename = lc.get_media(media_id).get("media_name")
            self.set_header("Content-Type", "application/octet-stream")
            self.set_header("Content-Disposition",
                            "attachment; filename=" + filename + ".lrc")

            self.write_content(media_list)
            self.finish()

        else:
            self.write("not exist")

    def fmt_time(self,seconds):
        seconds = round(seconds, 2)
        # t_start = datetime.datetime(1970, 1, 1)
        # t_delta = datetime.timedelta(seconds=seconds)
        # t_end = t_start + t_delta
        # time_tuple = (t_end.hour - t_start.hour,
        #               t_end.minute - t_start.minute,
        #               t_end.second - t_start.second,
        #               t_end.microsecond - t_start.microsecond)
        minute, second = divmod(seconds,60)
        return "[%s:%s]" % (str(int(minute)), str(second))

    def fmt_content(self, media):
        content_list = media.get(self.content_key)
        content = content_list[0] if content_list else ""
        content = re.sub(u"[,，。\.?？!！]"," ",content)
        return content

    def write_content(self, media_list):
        for (index, media) in enumerate(media_list, 1):
            self.write(self.fmt_time(media.get("start_at")))
            self.write(self.fmt_content(media))
            self.write("\n")


def make_app(use_autoreload):
    return tornado.web.Application([
        (r"/test", TestHandler),
        (r"/transcribe", TranscribeHandler),
        (r"/medium/(.*)/srt", SrtHandler),
        (r"/medium/(.*)/lrc", LrcHandler),
    ], autoreload=use_autoreload)


if __name__ == "__main__":
    """
    set system environ "PIPELINE_SERVICE_ENV"  to use different environment,
    choices are "develop product staging".
    or use command line option  %process_name  --env == [envname].
    """

    from tornado.options import define, options
    from tornado.netutil import bind_unix_socket

    # when python writes unicode to stdout,it will encode unicode string
    # using  sys.getdefaultencoding()
    # on a linux ,it defaults to ascii,so got an error like this
    # "UnicodeEncodeError: "ascii" codec can"t encode character  u"\uxxxx"
    # in position 183: ordinal not in range(128)"
    # use sys.getdefaultencoding() to get current val

    import sys

    reload(sys)
    sys.setdefaultencoding("utf-8")

    define("port", default=8888, help="run on this port", type=int)
    define("env", default="develop", help="develop production staging")
    define("use_autoreload", default=True, help="set debug to use auto reload")
    define("unix_socket", default=None, help="unix socket path")
    tornado.options.parse_command_line()

    env = os.environ.get("PIPELINE_SERVICE_ENV")
    if not env:
        env = options.env

    pwd = os.path.dirname(__file__)
    sys.path.append(pwd)
    config_file = os.path.join(pwd, "config", env + ".json")
    config_dict = json.load(open(config_file))
    env_config.init_config(config_dict)

    logging.info("------current environment is \"%s\","
                 "using config file: \"%s\"" % (env, config_file))

    # logging.info(env_config.CONFIG.__dict__)

    server = tornado.httpserver.HTTPServer(make_app(options.use_autoreload),
                                           xheaders=True)
    if options.unix_socket:
        server.add_socket(bind_unix_socket(options.unix_socket))
    else:
        server.listen(options.port)
    logging.info("running on %s" % (options.unix_socket or options.port))

    tornado.ioloop.IOLoop.instance().start()
