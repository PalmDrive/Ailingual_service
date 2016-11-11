# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from bosonnlp import BosonNLP
from ..task.summarization_task import SummarizationTask
from xiaobandeng.config import CONFIG
from tornado import concurrent
import logging
import traceback

class TaskBoson(SummarizationTask):

    def __init__(self, title, content, order=None, completion_callback=None):
        super(TaskBoson, self).__init__(title, content, order, completion_callback)

    def source_name(self):
        return 'boson'

    def start(self):
        try:
            f = self.get_request(self.title, self.content)
            f.add_done_callback(self.callback)
            return f
        except Exception as e:
            logging.exception('exception caught in performing boson summarization task %d' % self.order)
            traceback.print_exc()
            self.result = ['Summarization failed']
            self.complete()


    @concurrent.run_on_executor
    def get_request(self, title = '', content = ''):
        nlp = BosonNLP(CONFIG.BOSON_API_KEY)
        result = nlp.summary(title, content, word_limit=100, not_exceed=1)
        return result

    def callback(self, r):
        print("BosonNLP API result - " + r)
        self.result = r
        self.complete()

class BosonNLPService(object):
    def batch_summarization_tasks(self, titles, contents):
        for i in xrange(len(contents)):
            yield TaskBoson(titles[i], contents[i],
                            )
            #
            # def vop(self, file_name, lan):
            #     def callback(task):
            #         print task.result
            #
            #     task = TaskBaidu(self.access_token, file_name, 0, None, lan, callback)
            #     task.start()