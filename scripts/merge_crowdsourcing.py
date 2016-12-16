# coding:utf8
from __future__ import absolute_import

from xiaobandeng.config import load_config
from xiaobandeng.lean_cloud import init
from xiaobandeng.config import CONFIG
import leancloud

env = 'production'
load_config(env)
init(CONFIG)


Transcript = leancloud.Object.extend("Transcript")
transcript_query = Transcript.query


def find_all(media_id):
    transcript_query.equal_to("media_id", media_id)  # 01
    transcript_query.equal_to("set_type", "timestamp")
    transcript_query.add_ascending("start_at")
    transcript_query.limit(1000)
    return transcript_query.find()

    # print transcript_query.first().get("start_at"),
    # print transcript_query.first().get("end_at")
    # print transcript_query.count()


id_list = ["757817dc-2722-4eaf-9dc5-007510426ba1", #01  565
           "1a7d0839-146c-4e0f-8368-fc67a0a8718a", #02  612
           "5fec8db1-6106-4e81-a887-525e90fdfcc2"] #03  620


#orgin
orgin_media_id = "757817dc-2722-4eaf-9dc5-007510426666"
Media = leancloud.Object.extend("Media")
media_query = Media.query
media_query.equal_to("media_id", orgin_media_id)
media = media_query.first()

[find_all(id) for id in id_list]

# 1800.505918
# 1798.781837
# 2047.407187

def create(raw, offset):
    start_at = raw.get("start_at")
    end_at = raw.get("end_at")
    content_baidu = raw.get("content_baidu")

    t = Transcript()
    t.set("media_id", orgin_media_id)
    t.set("start_at", start_at+offset)
    t.set("end_at", end_at+offset)
    t.set("content_baidu", content_baidu)
    t.set("set_type", "timestamp")
    t.save()
    print 'start_at:', start_at+offset


results = find_all(id_list[0])
for res in results:
    create(res, 0)


results = find_all(id_list[1])
for res in results:
    create(res, 1800.505918)


results = find_all(id_list[2])
for res in results:
    create(res, 3599.287755)



