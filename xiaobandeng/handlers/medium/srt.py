# -*- coding: utf-8 -*-

from __future__ import absolute_import

import re
import datetime
from xiaobandeng.lean_cloud import lean_cloud

from ..base import BaseHandler


class SrtHandler(BaseHandler):
    def get(self, media_id):
        # source = self.get_argument("service_source", 0)
        platform = self.get_argument("plat", 'win')

        # lc_content_keys = ["content_baidu", "content_google"]
        # content_key = lc_content_keys[int(source)]

        lc = lean_cloud.LeanCloud()
        fragment_list = lc.get_list(media_id=media_id)
        media = lc.get_media(media_id)
        content_keys = ["content_" + i for i in media.get("service_providers")]
        if not content_keys:
            content_keys = ["content_baidu"]

        def convert_time(seconds):
            seconds = round(seconds, 3)
            t_start = datetime.datetime(1970, 1, 1)
            t_delta = datetime.timedelta(seconds=seconds)
            t_end = t_start + t_delta
            time_tuple = (t_end.hour - t_start.hour,
                          t_end.minute - t_start.minute,
                          t_end.second - t_start.second,
                          t_end.microsecond - t_start.microsecond)

            # print ":".join(["%02d"%i for i in time_tuple[:-1]]) + "," + \
            # "%d" % (time_tuple[-1] / 1000)

            return ":".join(["%02d" % i for i in time_tuple[:-1]]) + "," + \
                   "%03d" % (time_tuple[-1] / 1000)

        if platform == "win":
            sep = "\r\n"
            encoding = "gbk"
        else:
            sep = "\n"
            encoding = "utf8"

        if fragment_list:
            filename = media.get("media_name")
            self.set_header("Content-Type", "application/octet-stream")
            self.set_header("Content-Disposition",
                            "attachment; filename=" + filename + ".srt")

            for (index, fragment) in enumerate(fragment_list, 1):
                self.write(str(index))
                self.write(sep)

                self.write(
                    convert_time(fragment.get("start_at")) + " --> " +
                    convert_time(fragment.get("end_at")))
                self.write(sep)

                for content_key in content_keys:
                    content_list = fragment.get(content_key)

                    content = content_list[0] if content_list else ""
                    content = re.sub(u"[,，。\.?？!！]", " ", content)
                    self.write(content.encode(encoding))
                    self.write(sep)

                self.write(sep)
            self.finish()

        else:
            self.write("not exist")
