import sys
import tornado
import tornado.ioloop
import tornado.httpclient
import tornado.gen
import logging
import tempfile
import os
from xiaobandeng.medium import convertor
from xiaobandeng.medium import preprocessor
from xiaobandeng.medium import vad
from xiaobandeng.task.task import TaskGroup
from xiaobandeng.transcribe import baidu
from tornado.locks import Condition
from xiaobandeng.config import load_config
from xiaobandeng.daguan import daguan

condition = Condition()
content = []


@tornado.gen.coroutine
def download_audio(filename):
    client = tornado.httpclient.AsyncHTTPClient()
    response = yield client.fetch(filename)
    audio_file = write_to_file(response.body)
    raise tornado.gen.Return(audio_file)


def write_to_file(bs):
    tmp_file = tempfile.NamedTemporaryFile(suffix="mp3").name
    f = open(tmp_file, "wb")
    f.write(bs)
    f.close()
    logging.info("write file:%s" % tmp_file)
    return tmp_file


@tornado.gen.coroutine
def transcribe(audio_file):
    target_file = convertor.convert_to_wav(audio_file)

    audio_dir, starts, is_voices, break_pause = vad.slice(2, target_file)
    tarts, durations = preprocessor.preprocess_clip_length(
        audio_dir,
        starts,
        is_voices,
        break_pause,
        7,
        False,
    )

    basedir, subdir, files = next(os.walk(audio_dir))
    file_list = [os.path.join(basedir, file) for file in sorted(files)]
    task_group = TaskGroup(transcription_callback)
    baidu_speech_service = baidu.BaiduNLP()
    baidu_tasks = baidu_speech_service.batch_vop_tasks(
        file_list, starts, durations, "zh"
    )

    for task in baidu_tasks:
        task_group.add(task)

    task_group.start()
    yield condition.wait()
    print "wait"


def transcription_callback(task_group):
    for task in task_group.tasks:
        if len(task.result) == 0:
            continue
        content.append(task.result[0])
    condition.notify()


@tornado.gen.coroutine
def main():
    filename = sys.argv[1]
    audio_file = yield download_audio(filename)
    print audio_file
    yield transcribe(audio_file)
    uu = u' '.join(content)
    uu = uu.encode('utf-8')
    tags = yield daguan.tagging(uu)
    for tag in tags:
        print 'tag: ', tag['tag'], ' weight: ', tag['weight']


if __name__ == "__main__":
    load_config("develop")
    tornado.ioloop.IOLoop.instance().run_sync(main)
