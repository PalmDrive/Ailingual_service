# -*- coding: utf-8 -*-

from __future__ import absolute_import

from xiaobandeng.lean_cloud import lean_cloud

from ..base import BaseHandler


class TextHandler(BaseHandler):
    def get(self, media_id):
        service_provider = self.get_argument("service_provider", "baidu")

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

        all_transcript = lc.get_list(media_id, set_type_to_download)
        content_key = "content_" + service_provider

        if all_transcript:

            content = [transcript.get(content_key)[0] if transcript.get(
                content_key) else "" for transcript in
                       all_transcript]

            filename = media.get("media_name")
            self.set_header("Content-Type", "application/octet-stream")
            self.set_header("Content-Disposition",
                            "attachment; filename=" + filename + ".txt")
            self.write(''.join(content))
            self.finish()
        else:
            self.write("not exist")
