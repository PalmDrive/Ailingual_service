# coding: utf8
from __future__ import absolute_import
import uuid
from ..base import BaseHandler
from xiaobandeng.lean_cloud.lean_cloud import LeanCloud
from ..error_code import ECODE


class CaptionHandler(BaseHandler):
    def post(self, media_id):
        transcript_set = self.get_argument("transcript_set", "1")

        transcript_set_to_set_type_map = {
            "1": "machine",
            "2": "ut",
            "3": "timestamp"
        }
        lc = LeanCloud()
        media = lc.get_media(media_id)

        transcript_sets = media.get("transcript_sets")
        if transcript_sets.get("timestamp"):
            self.write_error(
                self.response_error(*ECODE.CAPTION_EXISTS_TRANSCRIPT))
            return

        all_transcript = lc.get_list(media_id, transcript_set_to_set_type_map[
            transcript_set])
        index = 0

        text = ""
        for transcript in all_transcript:
            try:
                content = transcript.get("content_baidu")[0]
                if not content:
                    continue
            except (TypeError, IndexError):
                continue
            content = content.replace(u"。", u"，")
            content = content.replace(u"？", u"，")
            content = content.replace(u"！", u"，")
            content = content.replace(u",", u"，")
            content = content.replace(u",", u"，")
            content = content.replace(u"?", u"，")
            content = content.replace(u"!", u"，")
            text += content

        caption_content_list = text.split(u"，")
        if caption_content_list[-1].strip() == "":
            caption_content_list.pop()

        for content in caption_content_list:
            fragment_order, start_at, end_at, media_id, fragment_src, set_type = (
                index, 0.00, 0.00, media_id, "", "timestamp")
            lc.set_fragment(fragment_order, start_at, end_at, media_id,
                            fragment_src, set_type)

            lc.add_transcription_to_fragment(index, content, "baidu")
            index += 1


        lc.fragments[0].set("start_at", 0.01)
        lc.save_fragments()

        transcript_sets["timestamp"] = 1

        print transcript_sets

        media.set("transcript_sets", transcript_sets)
        media.save()

        self.write(self.response_success())
        self.finish()
