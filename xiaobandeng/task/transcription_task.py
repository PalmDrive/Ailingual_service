# coding:utf8

from task import Task
import wave

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
        self.file_prepare()

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