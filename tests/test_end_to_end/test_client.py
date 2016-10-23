# coding:utf8

# Install the Python Requests library:
# `pip install requests`

import requests
from tornado.testing import AsyncHTTPTestCase
import tornado
import logging
logging.basicConfig(level=logging.DEBUG)
import unittest
from xiaobandeng.server import make_app
from xiaobandeng.config import CONFIG
from xiaobandeng.config import load_config
from xiaobandeng.lean_cloud import init
import urllib
import os

class ApiTestCase(AsyncHTTPTestCase):
    def get_app(self):
        self.app = make_app(False)
        return self.app

    def test_request(self):
        os.environ["ASYNC_TEST_TIMEOUT"] = "60"
        print(self.get_url('/'))
        load_config("develop")
        init(CONFIG)
        headers = {
            "app_key": "34363bc78d6c",
            "app_id": "e3f9e83a-91df-11e6-852f",
        }
        params = {
            "media_name": "test media - zh",
            "addr": "http://xiaobandeng-staging.oss-cn-hangzhou.aliyuncs.com/pipeline_videos/王东岳上午音频160-end.mp3",
            "lan": "zh",
            "company": "Ailingual",
        }
        query_string = urllib.urlencode(params)

        response = self.fetch(('/transcribe?%s' % query_string), method='GET', headers=headers, connect_timeout = 60, request_timeout = 60)
        print(response)
        print(response.body)
        self.assertEqual(response.code, 200)
        assert hasattr(response.body, "data")

    def send_async_request(self):
        try:
            response = requests.get(
                url="http://localhost:8888/transcribe",
                params={
                    "media_name": "test media - zh",
                    "addr": "http://xiaobandeng-staging.oss-cn-hangzhou.aliyuncs.com/pipeline_videos/王东岳上午音频160-end.mp3",
                    "lan": "zh",
                    "company": "Ailingual",
                    "async": "true",
                    "callback_url": "http://localhost:10000/test",
                },
                headers={
                    "app_key": "34363bc78d6c",
                    "app_id": "e3f9e83a-91df-11e6-852f",
                },
            )
            print('Response HTTP Status Code: {status_code}'.format(
                status_code=response.status_code))
            print('Response HTTP Response Body: {content}'.format(
                content=response.content))
        except requests.exceptions.RequestException:
            print('HTTP Request failed')

    def send_sync_request(self):
        try:
            response = requests.get(
                url="http://localhost:8888/transcribe",
                params={
                    "media_name": "test media - zh",
                    "addr": "http://xiaobandeng-staging.oss-cn-hangzhou.aliyuncs.com/pipeline_videos/王东岳上午音频160-end.mp3",
                    "lan": "zh",
                    "company": "Ailingual",
                },
                headers={
                    "app_key": "34363bc78d6c",
                    "app_id": "e3f9e83a-91df-11e6-852f",
                },
            )
            print('Response HTTP Status Code: {status_code}'.format(
                status_code=response.status_code))
            print('Response HTTP Response Body: {content}'.format(
                content=response.content))
        except requests.exceptions.RequestException:
            print('HTTP Request failed')


if __name__ == '__main__':
    unittest.main()
