# -*- coding: utf-8 -*-

from __future__ import absolute_import

import re
import datetime
from .download_base import DownloadHandler


class SrtHandler(DownloadHandler):
    def convert_time(self, seconds):
        seconds = round(seconds, 3)
        t_start = datetime.datetime(1970, 1, 1)
        t_delta = datetime.timedelta(seconds=seconds)
        t_end = t_start + t_delta
        time_tuple = (t_end.hour - t_start.hour,
                      t_end.minute - t_start.minute,
                      t_end.second - t_start.second,
                      t_end.microsecond - t_start.microsecond)

        return ":".join(["%02d" % i for i in time_tuple[:-1]]) + "," + \
               "%03d" % (time_tuple[-1] / 1000)

    def handle(self, media, fragment_list, content_keys, sep, encoding):

        if fragment_list:
            filename = media.get("media_name")
            self.set_header("Content-Type", "application/octet-stream")
            self.set_header("Content-Disposition",
                            "attachment; filename=" + filename + ".srt")

            for (index, fragment) in enumerate(fragment_list, 1):
                self.write(str(index))
                self.write(sep)

                self.write(
                    self.convert_time(fragment.get("start_at")) + " --> " +
                    self.convert_time(fragment.get("end_at")))
                self.write(sep)

                for content_key in content_keys:
                    content_list = fragment.get(content_key)

                    content = content_list[0] if content_list else ""
                    content = re.sub(u"[,，。?？!！]", " ", content)
                    content = content.replace(u'\xa0', " ")
                    try:
                        self.write(content.encode(encoding))
                    except UnicodeEncodeError:
                        for i in content:
                            try:
                                self.write(i.encode(encoding))
                            except UnicodeEncodeError:
                                self.write(i)

                    self.write(sep)
                self.write(sep)
            self.finish()

        else:
            self.write("not exist")
