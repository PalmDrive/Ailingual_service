from __future__ import absolute_import
import leancloud


# init leancloud
def init(cfg):
    APP_ID = cfg.LEANCLOUD_APP_ID
    MASTER_KEY = cfg.LEANCLOUD_MASTER_KEY
    leancloud.init(APP_ID, MASTER_KEY)
