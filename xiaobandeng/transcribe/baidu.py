# coding:utf8

import json
import datetime
import tornado.httpclient
from task import Task, TaskGroup

# from env_config import CONFIG

BAIDU_API_KEY = "Ki1wq6cYASyrFFgMNQtGAmz5"
BAIDU_SECRET_KEY = "1226a59f3407d28d924012d76ee2f691"


# #warn:
# #baidu oauth api  access token expires 30 days
# #


class TaskBaidu(Task):

    vop_url = "http://vop.baidu.com/server_api"
    lans = {"zh": ['zh', 'zh', 'zh', 'en', 'en', 'en'],
            "en": ['en', 'en', 'en', 'zh', 'zh', 'zh']
            }

    def __init__(self, token_list, tid, file_name, lan='zh'):
        super(TaskBaidu, self).__init__(tid, file_name)
        self.token = token_list[0]
        self.max_try = 6
        self._try = 0
        self.lan = lan
        self.url = self.get_url(lan)

    def start(self):
        print 'start baidu vop on %s' % self.file_name
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
            print 'retry %s...%s' % (self.id, datetime.datetime.now())
        else:
            self.complete()
            self.result = ''

    def callback(self, res):
        if res.error:
            print '%s error:%s' % (self.id, res.error)
            self.retry()
            return

        res = json.loads(res.body)

        if int(res['err_no']) in (3301, 3302):
            # print '%s baidu api error :%s'%(self.id,res['err_no'])
            self.retry()
            return

        if int(res['err_no']) == 0:
            self.result = res["result"][0]
            self.complete()
            # print '%s====>%s'%(self.id,self.result)
            return

        self.result = 'Baidu API error: %d %s' % (res['err_no'], res['err_msg'])
        self.complete()


class BaiduNLP(object):
    def __init__(self):
        self.auth_url = "https://openapi.baidu.com/oauth/2.0/token?" \
                        "grant_type=client_credentials&client_id=%s&" \
                        "client_secret=%s"
        self.vop_url = "http://vop.baidu.com/server_api"
        self.auth_url = self.auth_url % (BAIDU_API_KEY, BAIDU_SECRET_KEY)
        self.client = tornado.httpclient.AsyncHTTPClient()
        self.access_token = ""
        self.client.fetch(self.auth_url, self.cb_login)

    def task_list_done(task_list, num):
        print 'all_done..'
        for i in xrange(num):
            print '%s-->%s' % (i, task_list.get(i).result)

    def cb_login(self, res):
        if res.error:
            print 'error auth!!'
        else:
            info = json.loads(res.body)
            self.access_token = info['access_token']
            print 'baidu nlp token got!'

    def vop(self, file_list, callback, starts, lan):
        task_list = TaskGroup(file_list, lan, callback, starts)
        task_list.set_task_type(TaskBaidu, self.access_token)
        task_list.start()
        print datetime.datetime.now()

