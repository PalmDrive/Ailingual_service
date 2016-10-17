# -*- coding: utf-8 -*-

from __future__ import absolute_import

import re
import datetime
from xiaobandeng.lean_cloud import lean_cloud

from ..base import BaseHandler


class SrtHandler(BaseHandler):
    def get(self, media_id):
        source = self.get_argument("service_source", 0)

        lc_content_keys = ["content_baidu", "content_google"]
        content_key = lc_content_keys[int(source)]

        lc = lean_cloud.LeanCloud()
        media_list = lc.get_list(media_id=media_id)

        def convert_time(seconds):
            seconds = round(seconds, 3)
            t_start = datetime.datetime(1970, 1, 1)
            t_delta = datetime.timedelta(seconds=seconds)
            t_end = t_start + t_delta
            time_tuple = (t_end.hour - t_start.hour,
                          t_end.minute - t_start.minute,
                          t_end.second - t_start.second,
                          t_end.microsecond - t_start.microsecond)
            return ":".join([str(i) for i in time_tuple[:-1]]) + "," + \
                   "%d" % (time_tuple[-1] / 1000)

        if media_list:
            filename = lc.get_media(media_id).get("media_name")
            self.set_header("Content-Type", "application/octet-stream")
            self.set_header("Content-Disposition",
                            "attachment; filename=" + filename + ".srt")
            for (index, media) in enumerate(media_list, 1):
                self.write(str(media.get("fragment_order") + 1))
                self.write("\n")
                self.write(
                    convert_time(media.get("start_at")) + "	-->	" +
                    convert_time(media.get("end_at")))
                self.write("\n")

                content_list = media.get(content_key)

                content = content_list[0] if content_list else ""
                content = re.sub(u"[,，。\.?？!！]", " ", content)
                self.write(content)
                self.write("\n")
                self.write("\n")
            self.finish()

        else:
            self.write("not exist")
