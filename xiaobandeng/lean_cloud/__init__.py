from __future__ import absolute_import
import leancloud


# init leancloud
def init(cfg):
    APP_ID = cfg.LEANCLOUD_APP_ID
    APP_KEY = cfg.LEANCLOUD_APP_KEY
    MASTER_KEY = cfg.LEANCLOUD_MASTER_KEY
    leancloud.init(APP_ID,APP_KEY, MASTER_KEY)
