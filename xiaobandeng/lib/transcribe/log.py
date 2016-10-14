# coding:utf8

from __future__ import absolute_import
import leancloud
from xiaobandeng.config import CONFIG


class TranscriptionLog(object):
    def __init__(self):
        APP_ID = CONFIG.LEANCLOUD_APP_ID
        MASTER_KEY = CONFIG.LEANCLOUD_MASTER_KEY

        leancloud.init(APP_ID, MASTER_KEY)
        self.Log = leancloud.Object.extend("TranscriptionLog")
        self.log = self.Log()

    def add(self, log_content):
        for (k, v) in log_content.items():
            self.log.set(k, v)

        self.log.set("media_duration", log_content["media_duration"] or 0)
        self.log.set("notified_client", "yes" if log_content["notified_client"] else "no" )

    def save(self):
        try:
            self.log.save()
        except leancloud.LeanCloudError as e:
            print e
