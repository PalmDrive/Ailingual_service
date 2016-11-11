# coding=utf8

from __future__ import print_function, unicode_literals
from xiaobandeng.task.summarization_task import SummarizationTask
from xiaobandeng.config import CONFIG
import logging
import traceback
import argparse
import json
import tornado.httpclient

SUMMARY_URL = 'http://api.bosonnlp.com/summary/analysis'


class TaskBoson(SummarizationTask):

    def __init__(self, title, content, order=None, completion_callback=None):
        super(TaskBoson, self).__init__(title, content, order, completion_callback)
        self.client = self.get_client()

    def source_name(self):
        return 'boson'

    def start(self):
        try:
            logging.info('start boson summarization on task %s' % self.order)
            self.fetch(SUMMARY_URL)
        except Exception as e:
            logging.exception('exception caught in performing boson summarization task %d' % self.order)
            traceback.print_exc()
            self.result = ['Summarization failed']
            self.complete()

    def get_client(self):
        return tornado.httpclient.AsyncHTTPClient()

    def fetch(self, url):
        self.client.fetch(self.get_request(url), self.callback)

    def get_request(self, url):
        http_header = {'X-Token' : CONFIG.BOSON_API_KEY}

        source = {
            'not_exceed': 1,
            'percentage': 100,
            'title' : self.title,
            'content' : self.content
        }

        return tornado.httpclient.HTTPRequest(url=url, method='POST',
                                              connect_timeout=1200,
                                              request_timeout=12000,
                                              headers=http_header,
                                              body=json.dumps(source).encode('utf-8')
        )

    def callback(self, res):
        res = json.loads(res.body)
        logging.info('res %s' % res)
        self.result = [res]
        self.complete()


class BosonNLPService(object):
    def batch_summarization_tasks(self, titles, contents):
        for i in xrange(len(contents)):
            yield TaskBoson(titles[i], contents[i], i
                            )

    def summarize(self, title, content):
        def callback(task):
            print(task.result)

        task = TaskBoson(title, content, 0, callback)
        task.start()

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'title', help='title')
    parser.add_argument(
        'content', help='content')
    args = parser.parse_args()
    boson = BosonNLPService()
    boson.summarize(args.title, args.content)

