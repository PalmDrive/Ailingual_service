import tornado.ioloop
import tornado.web
import urllib
import tempfile
import vad
import baidu
import os
import lean_cloud


voice = baidu.BaiduNLP()
voice.init_access_token()


class TranslateHandler(tornado.web.RequestHandler):
    def get(self):
        addr = self.get_argument('addr')
        objectName = self.get_argument('object')
        lc = lean_cloud.LeanCloud(objectName)
        try:
            tmp_file = tempfile.NamedTemporaryFile().name + ".wav"
            urllib.urlretrieve(addr, tmp_file)
            audio_dir = vad.slice(2, tmp_file)

            start_at = 0

            for subdir, dirs, files in os.walk(audio_dir):
                for i, file in enumerate(files):
                    duration, result = voice.vop(os.path.join(subdir, file))
                    end_at = start_at + duration
                    lc.add(i, start_at, end_at, result)
                    start_at = end_at
            lc.upload()
        except Exception as e:
            self.set_status(500)
            self.finish({'error_msg': e.message})
            return

        self.write("good")


def make_app():
    return tornado.web.Application([
        (r"/translate", TranslateHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
