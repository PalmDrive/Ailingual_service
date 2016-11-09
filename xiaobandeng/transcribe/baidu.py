# coding:utf8

from __future__ import absolute_import

import datetime
import json
import logging
import urllib2
import traceback

import tornado.httpclient

from xiaobandeng.config import CONFIG

from ..task.task import TranscriptionTask

# warn:
# baidu oauth api  access token expires 30 days


class TaskBaidu(TranscriptionTask):
    vop_url = "http://vop.baidu.com/server_api"
    lans = {"zh": ['zh', 'zh', 'zh', 'zh', 'zh', 'zh'],
            "en": ['en', 'en', 'en', 'en', 'en', 'en']
    }

    def __init__(self, token, file_name, start_time, duration=None, order=None,
                 lan='zh', completion_callback=None):
        super(TaskBaidu, self).__init__(file_name, start_time, duration, order,
                                        lan, completion_callback)
        self.token = token
        self.max_try = 6
        self._try = 0
        self.url = self.get_url(self.lans[self.lan][self._try])
        self.client = self.get_client()

    def source_name(self):
        return 'baidu'

    def get_client(self):
        return tornado.httpclient.AsyncHTTPClient()

    def start(self):
        try:
            logging.info('start baidu vop on %s' % self.file_name)
            self.fetch(self.url)
        except Exception as e:
            logging.exception(
                'exception caught in performing baidu transcription task %d' % self.order)
            traceback.print_exc()
            self.result = ['Transcription failed']
            self.complete()

    def fetch(self, url):
        self.client.fetch(self.get_request(url), self.callback)

    def get_request(self, url):
        http_header = {'Content-Type': 'audio/wav; rate=%d' % self.rate,
                       'Content-Length': str(len(self.body)),
        }

        return tornado.httpclient.HTTPRequest(url=url, method='POST',
                                              connect_timeout=1200,
                                              request_timeout=12000,
                                              headers=http_header,
                                              body=self.body
        )

    def get_url(self, lan):
        return self.vop_url + '?cuid=' + '123442123233213' + '&token=' + \
               self.token + '&lan=' + lan

    def retry(self):
        self._try += 1
        if self._try < self.max_try:
            try:
                self.fetch(self.get_url(self.lans[self.lan][self._try]))
                logging.info('retry %s %s...%s' % (
                self.__class__, self.order, datetime.datetime.now()))
            except Exception as e:
                logging.exception(
                    'exception caught in retrying baidu transcription task %d' % self.order)
                traceback.print_exc()
                self.result = ['Transcription failed']
                self.complete()
        else:
            logging.exception(
                'out of retry quota in baidu transcription task %d' % self.order)
            self.result = []
            self.complete()

    def callback(self, res):
        if res.error:
            logging.info(
                '%s %s error:%s' % (self.__class__, self.order, res.error))
            self.retry()
            return

        res = json.loads(res.body)

        if int(res['err_no']) in (3301, 3302, 3303):
            # logging.info('%s baidu api error :%s'%(self.order ,res['err_no']))
            self.retry()
            return

        if int(res['err_no']) == 0:
            self.result = res["result"]
            self.complete()
            # logging.info('%s====>%s'%(self.order, self.result))
            return

        logging.log("BAIDU API ERROR:%s===>%s" % (res["err_no"],res["err_msg"]))
        self.result = [""]
        self.complete()


class BaiduNLP(object):
    token_tuple = ()
    TOKEN_EXPIRE = 28

    def __init__(self):
        self.auth_url = "https://openapi.baidu.com/oauth/2.0/token?" \
                        "grant_type=client_credentials&client_id=%s&" \
                        "client_secret=%s"
        self.vop_url = "http://vop.baidu.com/server_api"

        self.auth_url = self.auth_url % (
            CONFIG.BAIDU_API_KEY, CONFIG.BAIDU_SECRET_KEY)
        self.client = tornado.httpclient.AsyncHTTPClient()
        self.access_token = self.get_token()

    def init_token(self):
        # sync fetch auth token..
        res = urllib2.urlopen(self.auth_url)
        try:
            info = json.loads(res.read())
            BaiduNLP.token_tuple = info['access_token'], datetime.datetime.now()
            logging.info('baidu nlp token got!')
        except (ValueError, KeyError):
            logging.error('error when get baidu api token!')

    def get_token(self):
        cached_token = BaiduNLP.token_tuple
        if cached_token:
            delta_days = (datetime.datetime.now() - cached_token[1]).days
            if delta_days > self.TOKEN_EXPIRE:
                self.init_token()
        else:
            self.init_token()

        return BaiduNLP.token_tuple[0]

    # def vop(self, file_list, callback, starts, lan):
    # task_list = TaskGroup(file_list, lan, callback, starts)
    #     task_list.set_task_type(TaskBaidu, self.access_token)
    #     task_list.start()
    #     logging.info(datetime.datetime.now())

    def batch_vop_tasks(self, file_list, starts, durations, lan):
        for task_id, file_name in enumerate(file_list):
            for l in lan.split(','):
                yield TaskBaidu(self.access_token, file_name, starts[task_id],
                                durations[task_id], task_id, l)
                #
                # def vop(self, file_name, lan):
                #     def callback(task):
                #         print task.result
                #
                #     task = TaskBaidu(self.access_token, file_name, 0, None, lan, callback)
                #     task.start()
