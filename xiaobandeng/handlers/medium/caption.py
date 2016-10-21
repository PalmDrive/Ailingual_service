# coding: utf8
from __future__ import absolute_import

import uuid
from ..base import BaseHandler
from xiaobandeng.lean_cloud.lean_cloud import LeanCloud
import json


class CaptionHandler(BaseHandler):
    def get(self, media_id):
        lc = LeanCloud()
        media = lc.get_media(media_id)
        print dir(media)
        print '------------'
        caption_media_id = str(uuid.uuid4())
        media.set("caption_media_id", caption_media_id)
        media.save()

        lc.add_media(media.get("media_name"), caption_media_id,
                     media.get("media_src"), media.get("duration"),
                     media.get("company_name"), media.get("requirement")
        )

        caption_transcript_list = []
        all_transcript = lc.get_list(media_id)
        index = 0

        for transcript in all_transcript:
            content = transcript.get("content_baidu")[0]
            content = content.strip(u"，")
            caption_content_list = content.split(u"，")

            for content in caption_content_list:
                fragment_order, start_at, end_at, media_id, fragment_src = (
                    index, 0.00, 0.00, caption_media_id, "" )
                lc.set_fragment(fragment_order, start_at, end_at, media_id,
                                fragment_src)
                lc.add_transcription_to_fragment(index, content, "baidu")
                index += 1
        lc.save()

        self.write(json.dumps({
            "media_id": caption_media_id,
        }))

        self.finish()
