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

from urlparse import urlparse
from os.path import splitext

#import re, urlparse


voice = baidu.BaiduNLP()
voice.init_access_token()


def get_ext(url):
    """Return the filename extension from url, or ''."""
    parsed = urlparse(url)
    root, ext = splitext(parsed.path)
    return ext  # or ext[1:] if you don't want the leading '.'


class TranscribeHandler(tornado.web.RequestHandler):
    def get(self):
        addr = self.get_argument('addr')
        addr = urllib.quote(addr.encode('utf8'), ':/')

        media_name = self.get_argument('media_name').encode("utf8")
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
                    duration, result = voice.vop(os.path.join(subdir, file))
                    end_at = starts[i] + duration
                    print('transcript result of %s : %s, duration %f, end_at %f' % (file, result, duration, end_at))
                    lc.add(i, starts[i], end_at, result, media_name, media_id, addr)
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

def make_app():
    return tornado.web.Application([
        (r"/transcribe", TranscribeHandler),
    ])

if __name__ == "__main__":
    #app = make_app()
    #app.listen(8888)
    from tornado.options import define, options
    define("port", default=8888, help="run on this port", type=int)
    define("runmode", default="dev", help="dev gray prod")
    define("debug", default=True, help="is ddebug")
    tornado.options.parse_command_line()
    if options.debug:
        import tornado.autoreload
    tornado.httpserver.HTTPServer(make_app(), xheaders=True).listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

    
