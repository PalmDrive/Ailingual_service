from __future__ import absolute_import

from xiaobandeng.config import load_config
from xiaobandeng.lean_cloud import init
from xiaobandeng.config import CONFIG
from xiaobandeng.lean_cloud import lean_cloud

media_id_list = ['01cebbd9-ce85-4798-933b-432bc51d7844',
                 'c31b13ad-069f-4826-8e16-44bf7d78a1d3',
                 '6c05e738-cb89-45ba-b47f-5ef64ab97ba7',
                 'f7419a52-6173-425b-99ab-758424a0e10b',
                 'af8f3ad5-eb1a-4867-955e-100c92a30bbe',
                 'be749fe2-ec75-4855-a088-44755830948c',
                 '345ba370-3f48-44e2-b1e3-d6ba4fb8bd2e']

def migrage(src_media_id):

    env = 'develop'
    load_config(env)
    init(CONFIG)

    lc = lean_cloud.LeanCloud()
    media = lc.get_media(src_media_id)

    # print media._attributes
    query = media.relation("containedTranscripts").query
    # print query.count()
    query.limit(1000)
    transcripts = query.find()
    # ---------------------------------------
    env = 'product'
    load_config(env)
    init(CONFIG)

    lc = lean_cloud.LeanCloud()
    media_keys = ["media_name",
                  "media_id",
                  "media_src",
                  "duration",
                  "company_name",
                  "requirement",
                  "lan",
                  "service_providers",
    ]

    media_tuple = [media.get(i) for i in media_keys]
    lc.add_media(*media_tuple)

    media_requirement = media.get("requirement", [])
    lc.media.set("requirement", media_requirement)

    media_duration = media.get("duration", None)
    lc.media.set("duration", media_duration)
    lc.media.set("is_copied", False)

    for transcript in transcripts:
        fragment_keys = ["fragment_order", "start_at", "end_at", "media_id",
                         "fragment_src"]
        transcript_tuple = [transcript.get(i) for i in fragment_keys]
        fragments = lc.set_fragment(*transcript_tuple)
        lc.fragments[transcript.get("fragment_order")].set("content_baidu",
                                                           transcript.get(
                                                               "content_baidu",[]))
        lc.fragments[transcript.get("fragment_order")].set("content_google",
                                                           transcript.get(
                                                               "content_google",[]))
        lc.fragments[transcript.get("fragment_order")].set("fragment_src",
                                                           transcript.get(
                                                               "fragment_src",""))

    lc.save()


for i in media_id_list:
    migrage(i)

print "over"
