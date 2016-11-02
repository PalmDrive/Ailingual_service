# -*- coding: utf-8 -*-

from __future__ import absolute_import

import re
import datetime
from xiaobandeng.lean_cloud import lean_cloud

from ..base import BaseHandler


class LrcHandler(BaseHandler):
    def get(self, media_id):
        # source = self.get_argument("service_source", 0)
        platform = self.get_argument("plat", 'win')

        # lc_content_keys = ["content_baidu", "content_google"]
        # self.content_key = lc_content_keys[int(source)]
        lc = lean_cloud.LeanCloud()
        media = lc.get_media(media_id)
        service_providers = media.get("service_providers") or ["baidu"]
        self.content_keys = ["content_" + i for i in service_providers]

        if platform == "win":
            self.sep = "\r\n"
            self.encoding = "gbk"
        else:
            self.sep = "\n"
            self.encoding = "utf8"

        lc = lean_cloud.LeanCloud()
        media_list = lc.get_list(media_id=media_id)

        if media_list:
            filename = lc.get_media(media_id).get("media_name")
            self.set_header("Content-Type", "application/octet-stream")
            self.set_header("Content-Disposition",
                            "attachment; filename=" + filename + ".lrc")

            self.write_content(media_list)
            self.finish()

        else:
            self.write("not exist")

    def fmt_time(self, seconds):
        seconds = round(seconds, 2)
        minute, second = divmod(seconds, 60)
        return "[%s:%s]" % (str(int(minute)), str(second))

    def fmt_content(self, media):
        content_list = []
        for content_key in self.content_keys:
            contents = media.get(content_key)
            content = contents[0] if contents else ""
            content = re.sub(u"[,，。?？!！]", " ", content)
            content_list.append(content.encode(self.encoding ))

        return self.sep.join(content_list)

    def write_content(self, media_list):
        for (index, media) in enumerate(media_list, 1):
            self.write(self.fmt_time(media.get("start_at")))
            self.write(self.fmt_content(media))
            self.write(self.sep)
