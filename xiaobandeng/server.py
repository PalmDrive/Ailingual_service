from __future__ import absolute_import

import tornado.ioloop
import tornado.web
import urllib
import tempfile
import vad
import baidu
import os
import lean_cloud
import convertor
import shutil
from urlparse import urlparse
from os.path import splitext


voice = baidu.BaiduNLP()
voice.init_access_token()


def get_ext(url):
    """Return the filename extension from url, or ''."""
    parsed = urlparse(url)
    root, ext = splitext(parsed.path)
    return ext  # or ext[1:] if you don't want the leading '.'


class TranslateHandler(tornado.web.RequestHandler):
    def get(self):
        addr = self.get_argument('addr')
        course_name = self.get_argument('course_name')
        lc = lean_cloud.LeanCloud()
        try:
            ext = get_ext(addr)
            tmp_file = tempfile.NamedTemporaryFile().name + ext
            urllib.urlretrieve(addr, tmp_file)

            target_file = convertor.convert_to_wav(ext, tmp_file)

            audio_dir = vad.slice(0, target_file)

            start_at = 0

            for subdir, dirs, files in os.walk(audio_dir):
                for i, file in enumerate(files):
                    duration, result = voice.vop(os.path.join(subdir, file))
                    end_at = start_at + duration
                    lc.add(i, start_at, end_at, result, course_name)
                    start_at = end_at
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

        self.write("good")


def make_app():
    return tornado.web.Application([
        (r"/translate", TranslateHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
