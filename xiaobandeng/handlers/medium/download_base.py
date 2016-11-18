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

        self.handle(media, fragment_list, content_keys, sep,
                    encoding)



