# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os
import tornado.ioloop
import tornado.web
import tornado.httpserver
import urllib
import tempfile
import vad
import baidu
import lean_cloud
import convertor
import shutil
import preprocessor
import uuid
import json
import logging
import datetime

from urlparse import urlparse
from os.path import splitext

# import re, urlparse


voice = baidu.BaiduNLP()
voice.init_access_token()


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
                        "X-Requested-With, Content-Type",
                        "x-smartchat-key,client-source")
        self.set_header("Access-Control-Allow-Methods",
                        "PUT,POST,GET,DELETE,OPTIONS")
        self.set_header("Access-Control-Allow-Credentials", "true")

    def options(self):
        self.set_header("Allow", "GET,HEAD,POST,OPTIONS")


class TestHandler(BaseHandler):
    def get(self):
        self.write("test ok")


class TranscribeHandler(BaseHandler):
    def get(self):
        addr = self.get_argument('addr')
        addr = urllib.quote(addr.encode('utf8'), ':/')

        media_name = self.get_argument('media_name').encode("utf8")
        language = self.get_argument('lan')

        lc = lean_cloud.LeanCloud()
        media_id = str(uuid.uuid4())
        try:
            ext = get_ext(addr)
            tmp_file = tempfile.NamedTemporaryFile().name + ext
            urllib.urlretrieve(addr, tmp_file)

            target_file = convertor.convert_to_wav(ext, tmp_file)

            audio_dir, starts = vad.slice(0, target_file)

            starts = preprocessor.fixClipLength(audio_dir, starts)

            for subdir, dirs, files in os.walk(audio_dir):
                for i in range(0, len(files)):
                    file = "pchunk-%d.wav" % i
                    duration, result = voice.vop(os.path.join(subdir, file),
                                                 language)
                    end_at = starts[i] + duration
                    print(
                        'transcript result of %s : %s, duration %f, end_at %f' % (
                            file, result, duration, end_at))
                    lc.add(i, starts[i], end_at, result, media_name, media_id,
                           addr)
            lc.upload()
        except Exception as e:
            self.set_status(500)
            self.finish({'error_msg': e.message})
            return
        finally:
            try:
                shutil.rmtree(audio_dir, ignore_errors=True)
                os.remove(tmp_file)
                os.remove(target_file)
            except:
                pass
        self.write(json.dumps({
            "media_id": media_id
        }))


class MediumHandler(BaseHandler):
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
                                       (r"/medium/(.*)/srt", MediumHandler)
                                   ], autoreload=use_autoreload)


if __name__ == "__main__":
    # app = make_app()
    # app.listen(8888)
    from tornado.options import define, options
    from tornado.netutil import bind_unix_socket

    define("port", default=8888, help="run on this port", type=int)
    define("runmode", default="dev", help="dev gray prod")
    define("use_autoreload", default=True, help="set debug to use auto reload")
    define("unix_socket", default=None, help="unix socket path")
    tornado.options.parse_command_line()

    server = tornado.httpserver.HTTPServer(make_app(options.use_autoreload),
                                           xheaders=True)
    if options.unix_socket:
        server.add_socket(bind_unix_socket(options.unix_socket))
    else:
        server.listen(options.port)
    logging.info("running on %s" % (options.unix_socket or options.port))

    tornado.ioloop.IOLoop.instance().start()

