# -*- coding: utf-8 -*-

from __future__ import absolute_import
from .download_base import DownloadHandler


class TextHandler(DownloadHandler):
    def handle(self, media, fragment_list, content_keys, sep, encoding):

        if fragment_list:
            content_key = content_keys[0]
            content = [transcript.get(content_key)[0] if transcript.get(
                content_key) else "" for transcript in fragment_list]

            filename = media.get("media_name")
            self.set_header("Content-Type", "application/octet-stream")
            self.set_header("Content-Disposition",
                            "attachment; filename=" + filename + ".txt")
            self.write((''.join(content)).encode(encoding))
            self.finish()
        else:
            self.write("not exist")