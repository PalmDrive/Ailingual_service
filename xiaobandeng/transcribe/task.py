#coding:utf8
import wave
import datetime
import logging

class TaskGroup(object):
    def __init__(self, callback, *cb_args):
        self.tasks = []
        self.done = False
        self.callback = callback
        self.cb_args = cb_args

    def get(self, tid):
        return self.tasks[tid]

    def add(self, task):
        self.tasks.append(task)
        task.set_group(self)

    def check_all(self):
        #    called by task
        if all([t.done for t in self.tasks]):
            self.complete()

    def complete(self):
        self.callback(self, *self.cb_args)
        print 'task group completed @ %s' % datetime.datetime.now()

    def start(self):
        if len(self.tasks) == 0:
            self.complete()
        else:
            for t in self.tasks:
                t.start()
            print 'task group started @ %s' % datetime.datetime.now()


class Task(object):
    def __init__(self, completion_callback=None):
        self._task_group = None
        self.done = False
        self.result = ''
        self.completion_callback = completion_callback
        self.configure()

    def configure(self):
        pass

    def start(self):
        pass

    def set_group(self, task_group):
        self._task_group = task_group

    def complete(self):
        logging.info('task completed: %s' % self.result)
        self.done = True
        if self.completion_callback:
            self.completion_callback(self)
        if self._task_group:
            self._task_group.check_all()


class TranscriptionTask(Task):
    def __init__(self, file_name, start_time, order=None, lan='zh', completion_callback=None):
        super(TranscriptionTask, self).__init__(completion_callback)
        self.file_name = file_name
        self.lan = lan
        self.frames = None
        self.rate = 0
        self.body = ''
        self.duration = 0
        self.start_time = start_time
        self.order = order

        self.file_prepare()

    def file_prepare(self):
        wav = wave.open(self.file_name)
        self.frames = wav.getnframes()
        self.rate = wav.getframerate()
        self.body = wav.readframes(wav.getnframes())
        self.duration = self.frames / float(self.rate)
        wav.close()

    def source_name(self):
        pass