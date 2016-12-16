# coding:utf8
from __future__ import absolute_import

from xiaobandeng.config import load_config
from xiaobandeng.lean_cloud import init
from xiaobandeng.config import CONFIG
import leancloud

env = 'production'
load_config(env)
init(CONFIG)

Media = leancloud.Object.extend("Media")
media_query = Media.query

Company = leancloud.Object.extend("Company")
client = Company.create_without_data("5823d8242f301e005c3e33ad")  # 网易云课堂

media_query.equal_to("client", client)
media_list = media_query.find()

print "count:", media_query.count()

Transcript = leancloud.Object.extend("Transcript")
end_at_list = []
content_list = []
for media in media_list:
    media_id = media.get("media_id")

    transcript_query = Transcript.query
    transcript_query.equal_to("media_id", media_id)
    transcript_query.equal_to("set_type", "ut")
    transcript_query.add_descending("start_at")
    transcript_query.limit(1)

    transcript_list = transcript_query.find()

    if transcript_list:
        transcript = transcript_list[0]
        content = transcript.get("content_baidu")
        end_at = transcript.get("end_at")
        if not end_at:
            end_at_list.append(transcript)
        if content:
            content = content[0]
            end_at_list.append(transcript)
        else:
            content_list.append(transcript)
    else:
        continue

print 'content:',content_list
print 'end_at:',[media.get("media_name") + media.get("media_id")  for media in end_at_list]


import os
os.system("say - v Good News ok")