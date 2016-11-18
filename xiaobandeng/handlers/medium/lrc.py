# -*- coding: utf-8 -*-

from __future__ import absolute_import

import re
from .download_base import DownloadHandler


class LrcHandler(DownloadHandler):
    def handle(self, media, fragment_list, content_keys, sep, encoding):

        if fragment_list:
            filename = media.get("media_name")
            self.sep = sep
            self.encoding = encoding
            self.content_keys = content_keys

            self.set_header("Content-Type", "application/octet-stream")
            self.set_header("Content-Disposition",
                            "attachment; filename=" + filename + ".lrc")
            self.write_content(fragment_list)
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
            content_list.append(content.encode(self.encoding))

        return self.sep.join(content_list)

    def write_content(self, media_list):
        for (index, media) in enumerate(media_list, 1):
            self.write(self.fmt_time(media.get("start_at")))
            self.write(self.fmt_content(media))
            self.write(self.sep)
