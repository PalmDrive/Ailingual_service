#coding:utf8

import leancloud
from datetime import datetime
from env_config import CONFIG
import logging


class LeanCloud(object):
    def __init__(self):
        APP_ID = CONFIG.LEANCLOUD_APP_ID
        MASTER_KEY = CONFIG.LEANCLOUD_MASTER_KEY

        leancloud.init(APP_ID, MASTER_KEY)
        self.Fragment = leancloud.Object.extend("TranscriptionLog")
        self.fragments = {}
        self.fragment_query = self.Fragment.query


