# coding:utf8
# Install the Python Requests library:
# `pip install requests`

import requests
import urlparse
import os
import json
import urllib
import threading
import threadpool

def crete_task(media_id):
    # My API (5)
    # GET http://localhost:8888/medium/XXX/create_task
    try:
        response = requests.get(
            url="http://localhost:8888/medium/%s/create_task" % media_id,
        )
        print "create task..... media_id..%s" % media_id
        print('Response HTTP Status Code: {status_code}'.format(
            status_code=response.status_code))
        print('Response HTTP Response Body: {content}'.format(
            content=response.content))
    except requests.exceptions.RequestException:
        print('HTTP Request failed')


def send_request(addr):
    # My API (7)
    # GET http://localhost:8888/transcribe

    parse = urlparse.urlparse(addr)
    media_name = os.path.splitext(parse.path)[0].lstrip("/pipeline_videos/")

    try:
        response = requests.get(
            url="http://localhost:8888/transcribe",
            params={
                "media_name": media_name,
                "addr": addr,
                "company": "网易云课堂",
                "caption_type": "editor",
                "lan": "zh",
                "requirement": "字幕",
                "async":"false"
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
        res = json.loads(response.content)
        crete_task(res["data"]["media_id"])
        print 'ok------------------------------------------------>',media_name
        print "media_id:%s" % ( res["data"]["media_id"])


    except :
        print('HTTP Request failed')
        print 'failed-------------------------------------------------->',addr

    # "2.2.1 文本流.mp4",
    # "5-1.2 创建数组.mp4",
    # "2.2.2 汉字编码.mp4",
    # "5-1.3 数组的元素.mp4",
    # "2.2.3 格式化输入输出.mp4",
    # "5-1.4 投票统计.mp4",
    # "2.3.1 流的应用.mp4",
    # "5-2.1 数组变量.mp4",
    # "2.3.2 对象串行化.mp4",
    # "5-2.4 二维数组.mp4",
    # "7.1 抽象.mp4",
    # "7.2.1 细胞自动机.mp4",
    # "7.3.2 接口.mp4",
    # "8.2.1 JTable.mp4",
    # "4-3.2 最大公约数.mp4",
    # "5-1.1 初试数组.mp4",
    # "8.1.1 布局管理器.mp4",
    # "7.3.1 狐狸与兔子.mp4",
    # "7.2.2 数据与表现分离.mp4",
    # "7.3.3 接口设计模式.mp4",
#    "5-2.2 遍历数组.mp4",
#    "5-2.3 素数.mp4",#
#    "3-1.1 循环.mp4",#
#    "3-1.2 数数字.mp4",#
#    "3-1.3 while循环.mp4",#
#    "3-2.1 计数循环.mp4",#
#    "3-2.2 算平均数.mp4",#
#    "3-2.3 猜数游戏.mp4",#
#    "4-1.1 for循环.mp4",#
#    "4-1.2 复合赋值.mp4",#
#    "4-2.1 循环控制.mp4",#
#    "4-2.3 逻辑类型.mp4",#
#    "4-3.1 求和.mp4",#
#    "3-1.4 do-while循环.mp4",#
#    "3-2.4 整数分解.mp4",#

names = [
    "8.1.2 反转控制.mp4",#
    "8.1.3 内部类.mp4",#
    "4-2.2 多重循环.mp4",#
    "8.2.2 MVC设计模式.mp4",#
]

def trans():
    base = "http://ailingual-production.oss-cn-shanghai.aliyuncs.com/pipeline_videos/"
    pool = threadpool.ThreadPool(3)

    for name in names:
        uri =base + name
        request = threadpool.makeRequests(send_request, (uri,))
        pool.putRequest(request[0])
    pool.wait()

trans()