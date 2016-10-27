# coding:utf8

from __future__ import absolute_import

import datetime
import logging
import wave


PENDING_TASKS = 0


def current_pending_tasks():
    global PENDING_TASKS
    return PENDING_TASKS


def increase_pending_task(count=1):
    global PENDING_TASKS
    PENDING_TASKS += 1


def decrease_pending_task(count=1):
    global PENDING_TASKS
    PENDING_TASKS -= 1


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
        logging.info('task %s completed,result: %s' % (
            self.order, self.result[0] if len(self.result) > 0 else ""))
        decrease_pending_task(1)
        self.done = True
        if self.completion_callback:
            self.completion_callback(self)
        if self._task_group:
            self._task_group.check_all()


class TranscriptionTask(Task):
    def __init__(
        self,
        file_name,
        start_time,
        duration=None,
        order=None,
        lan='zh',
        completion_callback=None
    ):
        super(TranscriptionTask, self).__init__(completion_callback)
        self.file_name = file_name
        self.lan = lan
        self.frames = None
        self.rate = 0
        self.body = ''
        self.start_time = start_time
        self.order = order
        self.duration = duration

    def file_prepare(self):
        wav = wave.open(self.file_name)
        self.frames = wav.getnframes()
        self.rate = wav.getframerate()
        self.body = wav.readframes(wav.getnframes())
        if self.duration == None:
            self.duration = self.frames / float(self.rate)
        wav.close()

    def source_name(self):
        pass
