#coding:utf8
import wave
import tornado.httpclient
import tornado.ioloop
import datetime
import tornado.gen
import tornado.web


class TaskGroup(object):
    def __init__(self, file_list, lan, callback, *cb_args):
        self.task_dict = {}
        self.done = False
        self.callback = callback
        self.cb_args = cb_args
        self.file_list = file_list
        self.lan = lan
        self._task_type = None
        self.token_list = None

    def get(self, tid):
        return self.task_dict[tid]

    def add(self, tid, task):
        self.task_dict[tid] = task
        task.set_group(self)

    def check_all(self):
        #    called by task
        if all([t.done for t in self.task_dict.values()]):
            self.complete()

    def complete(self):
        self.callback(self, *self.cb_args)
        print 'task group completed @ %s' % datetime.datetime.now()

    def set_task_type(self, task_type, *token_list):
        self._task_type = task_type
        self.token_list = token_list

    def start(self):
        for task_id, file_name in enumerate(self.file_list):
            t = self._task_type(self.token_list, task_id, file_name, self.lan)
            self.add(task_id, t)
            t.start()
        print 'task group started @ %s' % datetime.datetime.now()


class Task(object):
    def __init__(self, task_id, file_name):
        self.id = task_id
        self.file_name = file_name

        self.frames = None
        self.rate = 0
        self.body = ''
        self.duration = 0

        self._task_group = None
        self.done = False
        self.result = ''
        self.client = self.get_client()

        self.file_prepare()
        self.configure()

    def configure(self):
        pass

    def start(self):
        pass

    def set_group(self, task_group):
        self._task_group = task_group

    def get_client(self):
        return tornado.httpclient.AsyncHTTPClient()

    def complete(self):
        self.done = True
        if self._task_group:
            self._task_group.check_all()

    def file_prepare(self):
        wav = wave.open(self.file_name)
        self.frames = wav.getnframes()
        self.rate = wav.getframerate()
        self.body = wav.readframes(wav.getnframes())
        self.duration = self.frames / float(self.rate)
        wav.close()

