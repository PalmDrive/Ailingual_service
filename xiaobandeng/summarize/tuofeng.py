# coding=utf8

from __future__ import print_function, unicode_literals
from xiaobandeng.task.summarization_task import SummarizationTask
from xiaobandeng.config import CONFIG
import logging
import traceback
import argparse
import json
import tornado.httpclient
import urllib

SUMMARY_URL = 'http://api.tuofeng.cn/zhaiyao/v2/article'


class TaskTuofeng(SummarizationTask):
	def __init__(self, title, content, order=None, completion_callback=None):
		super(TaskTuofeng, self).__init__(title, content, order, completion_callback)
		self.client = self.get_client()

	def source_name(self):
		return 'tuofeng'

	def start(self):
		try:
			logging.info('start Tuofeng summarization on task %s' % self.order)
			self.fetch(SUMMARY_URL)
		except Exception as e:
			logging.exception('exception caught in performing Tuofeng summarization task %d' % self.order)
			traceback.print_exc()
			self.result = ['Summarization failed']
			self.complete()

	def get_client(self):
		return tornado.httpclient.AsyncHTTPClient()

	def fetch(self, url):
		self.client.fetch(self.get_request(url), self.callback)

	def get_request(self, url):

		params = {
			"key": CONFIG.TUOFENG_API_KEY,
			"title": self.title,
			"content": self.content,
			"size": 100,
		}
		query_string = urllib.urlencode(params)

		url_string = url + "?" + query_string

		return tornado.httpclient.HTTPRequest(url=url_string, method='GET',
		                                      connect_timeout=1200,
		                                      request_timeout=12000)

	def callback(self, res):
		r = json.loads(res.body)

		if r.get('error') == None:
			logging.info('res %s' % r)
			self.result = [r.get('summary')]
		else:
			logging.info('error %s' % json.dumps(r.get('error')))
			self.result = []
		self.complete()

class TuofengNLPService(object):
	def batch_summarization_tasks(self, titles, contents):
		for i in xrange(len(contents)):
			yield TaskTuofeng(titles[i], contents[i], i
			                  )

	def summarize(self, title, content):
		def callback(task):
			print(task.result)

		task = TaskTuofeng(title, content, 0, callback)
		task.start()


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument(
		'title', help='title')
	parser.add_argument(
		'content', help='content')
	args = parser.parse_args()
	boson = TuofengNLPService()
	boson.summarize(args.title, args.content)
