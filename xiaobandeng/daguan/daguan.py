# coding:utf8

from __future__ import absolute_import

import tornado
from tornado.httpclient import AsyncHTTPClient
import tornado.gen
import urllib
import json


TAG_URL = "http://taggingapi.datagrand.com/tagging/xiaobandeng"
APP_ID = 2273641


@tornado.gen.coroutine
def tagging(content=u'c', title=""):
    global TAG_URL
    global APP_ID
    params = {
        "appid": APP_ID,
        "text": content,
    }
    http_client = AsyncHTTPClient()
    body = urllib.urlencode(params)
    response = yield http_client.fetch(TAG_URL, method='POST', body=body)
    body = json.loads(response.body, encoding='utf-8')
    raise tornado.gen.Return(body['tag_list'])


if __name__ == '__main__':
    tornado.ioloop.IOLoop.instance().run_sync(tagging)
