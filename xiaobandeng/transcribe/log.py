# coding:utf8

import leancloud
from env_config import CONFIG


class TranscriptionLog(object):
    def __init__(self):
        APP_ID = CONFIG.LEANCLOUD_APP_ID
        MASTER_KEY = CONFIG.LEANCLOUD_MASTER_KEY

        leancloud.init(APP_ID, MASTER_KEY)
        self.Log = leancloud.Object.extend("TranscriptionLog")
        self.log = self.Log()

    def add(self, log_content):
        self.log.set("request_start_timestamp", log_content["request_start_timestamp"])
        self.log.set("request_end_timestamp", log_content["request_end_timestamp"])
        self.log.set("transcribe_end_timestamp", log_content["transcribe_end_timestamp"])

        self.log.set("result", log_content["result"])
        self.log.set("status", log_content["status"])


        self.log.set("media_duration", log_content["media_duration"] or 0)
        self.log.set("notified_client", "yes" if log_content["notified_client"] else "no" )
        self.log.set("headers", log_content["headers"])

        self.log.set("arguments_get", log_content["arguments_get"])
        self.log.set("arguments_post", log_content["arguments_post"])
        self.log.set("ip", log_content["ip"])
        self.log.set("agent", log_content["agent"])
        self.log.set("path", log_content["path"])
        self.log.set("uri", log_content["uri"])
        self.log.set("method", log_content["method"])

        self.log.save()


    def save(self):
        try:
            self.log.save()
        except leancloud.LeanCloudError as e:
            print e

