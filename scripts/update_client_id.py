# coding:utf8
from __future__ import absolute_import

from xiaobandeng.config import load_config
from xiaobandeng.lean_cloud import init
from xiaobandeng.config import CONFIG
import leancloud
env = 'production'
load_config(env)
init(CONFIG)

CLASS_NAME = 'Media'

lean_cloud_class = leancloud.Object.extend(CLASS_NAME)
query = lean_cloud_class.query

Company = leancloud.Object.extend("Company")

query.equal_to("company_name","网易云课堂")
query.limit(1000)

media_list = query.find()

client = Company.create_without_data("5823d8242f301e005c3e33ad")

for media  in media_list:
    media.set("client",client)
    media.save()

import os
os.system("say ok")