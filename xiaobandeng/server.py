# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os
import tornado.gen
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
import functools
import oss
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor
from transcribe import baidu, google
from transcribe.task import TaskGroup, TranscriptionTask
import wave
import multiprocessing

from urlparse import urlparse
from os.path import splitext

# import re, urlparse


def get_ext(url):
    """Return the filename extension from url, or ''."""
    parsed = urlparse(url)
    root, ext = splitext(parsed.path)
    return ext  # or ext[1:] if you don't want the leading '.'


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
        # 服务器端必须指定允许请求的域名,不能使用'*'.否则无效
        # self.set_header("Access-Control-Allow-Credentials", "true")

    def options(self):
        self.set_header("Allow", "GET,HEAD,POST,PUT,DELETE,OPTIONS")


class TestHandler(BaseHandler):
    def get(self):
        self.write("test ok")


class TranscribeHandler(BaseHandler):

    executor = ThreadPoolExecutor(5)

    @run_on_executor
    def upload_oss_in_thread(self,media_id,file_list):
        #since oss api uses requests lib,the socket can not be selected by epoll
        #now use a thread to make it run concurrently.
        #but
        oss.upload(media_id, file_list)
        print '-----upload oss over-------'

    def write_file(self, response, file_name):
        f = open(file_name, 'wb')
        f.write(response.body)
        f.close()
        logging.info('write file:%s' % file_name)

    def transcription_callback(self, task_list):
        for task in task_list.tasks:
            end_at = task.start_time + task.duration
            results = task.result
            # print(
            #     u'transcript result of %s : %s, duration %f, end_at %f' %
            #     (task.file_name, result, duration, end_at))
            fragment_src = oss.media_fragment_url(self.media_id, task.file_name)
            self.cloud_db.set_fragment(task.order, task.start_time, end_at, self.media_id, fragment_src)
            for result in results:
                self.cloud_db.add_transcription_to_fragment(task.order, result, task.source_name())

        self.cloud_db.save()
        self.write(json.dumps({
            "media_id": self.media_id
        }))
        self.finish()

    def on_donwload(self, tmp_file, ext, language, response):
        if response.error:
            self.write('download error:%s'%str(response.code))
            self.finish()

        self.write_file(response, tmp_file)

        target_file = convertor.convert_to_wav(ext, tmp_file)

        wav = wave.open(target_file)
        duration = wav.getnframes() / float(wav.getframerate())
        wav.close()

        self.cloud_db = lean_cloud.LeanCloud()
        self.cloud_db.add_media(self.media_name, self.media_id, self.addr, duration, self.company_name)

        audio_dir, starts = vad.slice(0, target_file)
        if self.fragment_length_limit:
            starts = preprocessor.preprocess_clip_length(audio_dir, starts,
                                                         self.fragment_length_limit)
        else:
            starts = preprocessor.preprocess_clip_length(audio_dir, starts)

        basedir, subdir, files = next(os.walk(audio_dir))
        file_list = [os.path.join(basedir, file) for file in sorted(files)]

        # Upload media clips to Aliyun OSS
        if self.upload_oss:
            tornado.ioloop.IOLoop.instance().add_callback(
                                    functools.partial(self.upload_oss_in_thread,
                                                      self.media_id, file_list
                                                      )
                                    )

        # create a task group to organize transcription tasks
        task_group = TaskGroup(self.transcription_callback)

        if 'baidu' in self.service_providers:
            baidu_speech_service = baidu.BaiduNLP()
            baidu_tasks = baidu_speech_service.batch_vop_tasks(file_list, starts, language)
            for task in baidu_tasks:
                task_group.add(task)

        num_workers = multiprocessing.cpu_count()
        pool = multiprocessing.Pool(num_workers)
        if 'google' in self.service_providers:
            google_speech_servce = google.GoogleASR(pool)
            google_tasks = google_speech_servce.batch_vop_tasks(file_list, starts, language)
            for task in google_tasks:
                task_group.add(task)

        task_group.start()


    @tornado.web.asynchronous
    def get(self):
        addr = self.get_argument('addr')
        addr = urllib.quote(addr.encode('utf8'), ':/')

        media_name = self.get_argument('media_name').encode("utf8")
        language = self.get_argument('lan', 'zh')
        company_name = self.get_argument('company').encode("utf8")
        fragment_length_limit = self.get_argument('max_fragment_length', 10)
        if fragment_length_limit:
            fragment_length_limit = int(fragment_length_limit)
        upload_oss = self.get_argument('upload_oss', False)
        if upload_oss == 'true' or upload_oss == 'True':
            upload_oss = True
        else:
            upload_oss = False
        service_providers = self.get_argument('service_providers', 'baidu').split(',')

        self.addr = addr
        self.media_name = media_name
        self.media_id = str(uuid.uuid4())
        self.language = language
        self.company_name = company_name
        self.fragment_length_limit = fragment_length_limit
        self.upload_oss = upload_oss
        self.service_providers = service_providers

        # try:
        ext = get_ext(addr)
        tmp_file = tempfile.NamedTemporaryFile().name + ext
        # urllib.urlretrieve(addr, tmp_file)
        client = tornado.httpclient.AsyncHTTPClient()
        client.fetch(addr,
                     callback=functools.partial(self.on_donwload,
                                                tmp_file, ext, language),
                     connect_timeout=120,
                     request_timeout=600)


class SrtHandler(BaseHandler):
    def get(self, media_id):
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
            filename = media_list[0].get("media_name")
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
                content = media.get("content")
                content = content.replace(",", " ")
                content = content.replace(u"，", " ")
                self.write(content)
                self.write("\n")
                self.write("\n")
            self.finish()

        else:
            self.write("not exist")


def make_app(use_autoreload):
    return tornado.web.Application([
        (r"/test", TestHandler),
        (r"/transcribe", TranscribeHandler),
        (r"/medium/(.*)/srt", SrtHandler)
    ], autoreload=use_autoreload)


if __name__ == "__main__":
    '''
    set system environ "PIPELINE_SERVICE_ENV"  to use different environment,
    choices are 'develop product staging'.
    or use command line option  %process_name  --env == [envname].
    '''

    import env_config
    from tornado.options import define, options
    from tornado.netutil import bind_unix_socket

    define("port", default=8888, help="run on this port", type=int)
    define("env", default="develop", help="develop production staging")
    define("use_autoreload", default=True, help="set debug to use auto reload")
    define("unix_socket", default=None, help="unix socket path")
    tornado.options.parse_command_line()

    env = os.environ.get("PIPELINE_SERVICE_ENV")
    if not env:
        env = options.env

    pwd = os.path.dirname(__file__)

    config_file = os.path.join(pwd, "config", env + ".json")
    config_dict = json.load(open(config_file))
    env_config.init_config(config_dict)

    logging.info("current env is %s" % env)
    logging.info("Using config file %s" % config_file)

    # logging.info(env_config.CONFIG.__dict__)

    server = tornado.httpserver.HTTPServer(make_app(options.use_autoreload),
                                           xheaders=True)
    if options.unix_socket:
        server.add_socket(bind_unix_socket(options.unix_socket))
    else:
        server.listen(options.port)
    logging.info("running on %s" % (options.unix_socket or options.port))

    tornado.ioloop.IOLoop.instance().start()

