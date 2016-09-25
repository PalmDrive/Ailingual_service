# coding:utf8
import json
import wave
import tornado.httpclient
import tornado.ioloop
import datetime
import tornado.gen
import tornado.web

Api_Key = "Ki1wq6cYASyrFFgMNQtGAmz5"
Secret_Key = "1226a59f3407d28d924012d76ee2f691"

# #warn:
# #baidu oauth api  access token  expires 30days
# #



class TaskList(object):
    def __init__(self, callback, starts):
        self.task_dict = {}
        self.done = False
        self.callback = callback
        self.starts = starts

    def get(self, tid):
        return self.task_dict[tid]

    def add(self, tid, task):
        self.task_dict[tid] = task
        task._task_list = self

    def check_all(self):
        '''
        called by task
        '''
        if all([t.done for t in self.task_dict.values()]):
            self.set_done()

    def set_done(self):
        self.callback(self, self.starts)
        print datetime.datetime.now()


class Task(object):
    max_try = 6
    lans = {"zh": ['zh', 'zh', 'zh', 'en', 'en', 'en'],
            "en": ['en', 'en', 'en', 'zh', 'zh', 'zh']
    }
    vop_url = "http://vop.baidu.com/server_api"

    def __init__(self, token, tid, file_name, lan='zh'):
        self.id = tid
        self.file_name = file_name
        self.lan = lan
        self.token = token
        self.url = self.vop_url + '?cuid=' + '123442123233213' + '&token=' + \
                   self.token + '&lan=' + self.lan

        wav = wave.open(file_name)
        frames = wav.getnframes()
        rate = wav.getframerate()
        self.duration = frames / float(rate)
        body = wav.readframes(wav.getnframes())
        wav.close()

        http_header = {
            'Content-Type': 'audio/wav; rate=%d' % rate,
            'Content-Length': str(len(body)),
        }

        self.header = http_header
        self.req = tornado.httpclient.HTTPRequest(url=self.url, method='POST',
                                                  connect_timeout=120,
                                                  request_timeout=600,
                                                  headers=self.header, body=body
        )
        self.client = tornado.httpclient.AsyncHTTPClient()

        self.done = False
        self.result = ''
        self._try = 0

    def fetch(self):
        self.client.fetch(self.req, self.callback)

    def set_lan(self, lan):
        self.url = self.vop_url + '?cuid=' + '123442123233213' + '&token=' + \
                   self.token + '&lan=' + lan

    def set_done(self):
        self.done = True
        if self._task_list:
            self._task_list.check_all()


    def retry(self):
        self._try += 1
        if self._try < self.max_try:
            self.set_lan(self.lans[self.lan][self._try])
            print 'retry %s...%s' % (self.id, datetime.datetime.now())
            self.fetch()
        else:
            self.set_done()
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

        if (int(res['err_no']) == 0):
            self.result = res["result"][0]
            self.set_done()
            # print '%s====>%s'%(self.id,self.result)
            return

        self.set_done()
        self.result = 'Baidu API error: %d %s' % (res['err_no'], res['err_msg'])


class BaiduNLP(object):
    def __init__(self):
        self.auth_url = "https://openapi.baidu.com/oauth/2.0/token?grant_type=client_credentials&client_id=%s&client_secret=%s"
        self.vop_url = "http://vop.baidu.com/server_api"
        self.auth_url = self.auth_url % (Api_Key, Secret_Key)
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
            print 'token got!'

    def vop(self, file_list, callback, starts, lan):
        task_list = TaskList(callback, starts)

        for i,file_name in enumerate(file_list):
            t = Task(self.access_token, i, file_name, lan)
            task_list.add(i, t)
            t.fetch()

        print datetime.datetime.now()



        # tornado.ioloop.IOLoop.instance().start()