# coding:utf8

import json
import datetime
import tornado.httpclient
from env_config import CONFIG
from task import TaskGroup, TranscriptionTask
import urllib2
import logging

# #warn:
# #baidu oauth api  access token expires 30 days
# #


class TaskBaidu(TranscriptionTask):

    vop_url = "http://vop.baidu.com/server_api"
    lans = {"zh": ['zh', 'zh', 'zh', 'zh', 'zh', 'zh'],
            "en": ['en', 'en', 'en', 'en', 'en', 'en'],
            "zh,en": ['zh', 'zh', 'zh', 'en', 'en', 'en'],
            "en,zh": ['en', 'en', 'en', 'zh', 'zh', 'zh'],
            }

    def __init__(self, token, file_name, start_time, order=None, lan='zh', completion_callback=None):
        super(TaskBaidu, self).__init__(file_name, start_time, order, lan, completion_callback)
        self.token = token
        self.max_try = 6
        self._try = 0
        self.url = self.get_url(lan)
        self.client = self.get_client()

    def source_name(self):
        return 'baidu'

    def get_client(self):
        return tornado.httpclient.AsyncHTTPClient()

    def start(self):
        logging.info('start baidu vop on %s' % self.file_name)
        self.fetch(self.url)

    def fetch(self, url):
        self.client.fetch(self.get_request(url), self.callback)

    def get_request(self, url):
        http_header = {'Content-Type': 'audio/wav; rate=%d' % self.rate,
                       'Content-Length': str(len(self.body)),
                       }

        return tornado.httpclient.HTTPRequest(url=url, method='POST',
                                              connect_timeout=120,
                                              request_timeout=600,
                                              headers=http_header,
                                              body=self.body
                                              )

    def get_url(self, lan):
        return self.vop_url + '?cuid=' + '123442123233213' + '&token=' + \
            self.token + '&lan=' + lan

    def retry(self):
        self._try += 1
        if self._try < self.max_try:
            self.fetch(self.get_url(self.lans[self.lan][self._try]))
            logging.info('retry %s %s...%s' % (self.__class__, self.order, datetime.datetime.now()))
        else:
            self.complete()
            self.result = ''

    def callback(self, res):
        if res.error:
            logging.info('%s %s error:%s' % (self.__class__, self.order, res.error))
            self.retry()
            return

        res = json.loads(res.body)

        if int(res['err_no']) in (3301, 3302):
            # logging.info('%s baidu api error :%s'%(self.order ,res['err_no']))
            self.retry()
            return

        if int(res['err_no']) == 0:
            self.result = res["result"][0]
            self.complete()
            # logging.info('%s====>%s'%(self.order, self.result))
            return

        self.result = 'Baidu API error: %d %s' % (res['err_no'], res['err_msg'])
        self.complete()


class BaiduNLP(object):
    def __init__(self):
        self.auth_url = "https://openapi.baidu.com/oauth/2.0/token?" \
                        "grant_type=client_credentials&client_id=%s&" \
                        "client_secret=%s"
        self.vop_url = "http://vop.baidu.com/server_api"

        self.auth_url = self.auth_url % (CONFIG.BAIDU_API_KEY, CONFIG.BAIDU_SECRET_KEY)
        self.client = tornado.httpclient.AsyncHTTPClient()
        self.access_token = ""
        # self.client.fetch(self.auth_url, self.cb_login)
        self.init_token()

    def task_list_done(task_list, num):
        logging.info('all_done..')
        for i in xrange(num):
            logging.info('%s-->%s' % (i, task_list.get(i).result))

    def init_token(self):
        res=urllib2.urlopen(self.auth_url)
        try:
            info = json.loads(res.read())
            self.access_token = info['access_token']
            logging.info('baidu nlp token got!')
        except (ValueError,  KeyError):
            logging.error('error when get baidu api token!')

    def batch_vop(self, file_list, callback, starts, lan):
        task_list = TaskGroup(callback)
        for task_id, file_name in enumerate(file_list):
            task = TaskBaidu(self.access_token, file_name, starts[task_id], task_id, lan)
            task_list.add(task)
        task_list.start()
        logging.info(datetime.datetime.now())

    def batch_vop_tasks(self, file_list, starts, lan):
        for task_id, file_name in enumerate(file_list):
            yield TaskBaidu(self.access_token, file_name, starts[task_id], task_id, lan)

    def vop(self, file_name, lan):
        def callback(task):
            print task.result

        task = TaskBaidu(self.access_token, file_name, 0, None, lan, callback)
        task.start()
