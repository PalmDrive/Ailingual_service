# -*- coding: utf-8 -*-

from __future__ import absolute_import

import re
import datetime
from xiaobandeng.lean_cloud import lean_cloud

from ..base import BaseHandler


class DownloadHandler(BaseHandler):
    def get(self, media_id):
        # source = self.get_argument("service_source", 0)
        platform = self.get_argument("plat", 'win')

        # lc_content_keys = ["content_baidu", "content_google"]
        # content_key = lc_content_keys[int(source)]

        lc = lean_cloud.LeanCloud()
        media = lc.get_media(media_id)
        self.media = media
        transcript_sets_map = media.get("transcript_sets")

        set_type_order = ["timestamp", "ut", "machine"]

        set_type_to_download = "machine"
        for set_type in set_type_order:
            if transcript_sets_map.get(set_type):
                set_type_to_download = set_type
                break
        print  'set type :%s' % set_type_to_download

        fragment_list = lc.get_list(media_id, set_type_to_download)
        provider_list = media.get("service_providers") or ["baidu"]
        content_keys = ["content_" + i for i in provider_list]

        if platform == "win":
            sep = "\r\n"
            encoding = "gbk"
        else:
            sep = "\n"
            encoding = "utf8"

        self.prepare_fragment_list(fragment_list)

        self.handle(media, fragment_list, content_keys, sep,
                    encoding)

    def prepare_fragment_list(self, fragment_list):

        company = self.media.get("client")
        company.fetch()

        for fragment in fragment_list:
            content = fragment.get("content_baidu", [""])[0]
            if company.get("name") == u"网易云课堂":
                # 对于网易云课堂的去掉语气助词
                #啊|啦|唉|呢|吧|了|哇|呀|吗||哦|哈|哟|么
                re_mood_words = u'\u554a|\u5566|\u5509|\u5462|\u5427|\u4e86|\u54c7|\u5440|\u5417|\u54e6|\u54c8|\u54df|\u4e48'
                baidu_content = re.subn(re_mood_words, "", content)[0]
                fragment.set("content_baidu", [baidu_content])
