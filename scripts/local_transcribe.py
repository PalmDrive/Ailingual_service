#coding:utf8
# Install the Python Requests library:
# `pip install requests`

import requests
import urlparse
import os
import urllib

def send_request(addr):
    # My API (7)
    # GET http://localhost:8888/transcribe

    parse = urlparse.urlparse(addr)
    media_name = os.path.splitext(parse.path)[0]

    try:
        response = requests.get(
            url="http://localhost:8888/transcribe",
            params={
                "media_name":media_name,
                "addr": addr,
                "async": "true",
                "company": "网易云课堂",
                "caption_type": "editor",
                "lan": "zh",
                "requirement": "字幕",
                "callback_url": "http://baidu.com",
            },
            headers={
                "app_key": "34399bc78d6c",
                "app_id": "e3f9e83a-91df-11e6-852f",
            },
        )
        print('Response HTTP Status Code: {status_code}'.format(
            status_code=response.status_code))
        print('Response HTTP Response Body: {content}'.format(
            content=response.content))
    except requests.exceptions.RequestException:
        print('HTTP Request failed')



file_url = [
'http://ailingual-production.oss-cn-shanghai.aliyuncs.com/pipeline_videos/1.2.3%20%E5%BC%82%E5%B8%B8%E6%8D%95%E6%8D%89%E6%97%B6%E7%9A%84%E5%8C%B9%E9%85%8D.mp4'
]

def trans():
    for url in file_url:
        send_request(urllib.unquote(url))

trans()

