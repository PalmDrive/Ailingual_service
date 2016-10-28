# -*- coding: utf-8 -*-

from __future__ import absolute_import

from xiaobandeng.lean_cloud import lean_cloud

from ..base import BaseHandler


class TextHandler(BaseHandler):
    def get(self, media_id):
        service_provider = self.get_argument("service_provider", "baidu")

        lc = lean_cloud.LeanCloud()
        all_transcript = lc.get_list(media_id=media_id)
        media = lc.get_media(media_id)
        content_key = "content_" + service_provider

        if all_transcript:
            content = [transcript.get(content_key)[0] for transcript in
                       all_transcript if transcript.get(content_key, [""])]

            filename = media.get("media_name")
            self.set_header("Content-Type", "application/octet-stream")
            self.set_header("Content-Disposition",
                            "attachment; filename=" + filename + ".txt")
            self.write(''.join(content))
            self.finish()
        else:
            self.write("not exist")
