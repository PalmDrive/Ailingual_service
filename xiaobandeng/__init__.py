from __future__ import absolute_import

from .env_config import CONFIG
import leancloud


# init leancloud
def init():
    APP_ID = CONFIG.LEANCLOUD_APP_ID
    MASTER_KEY = CONFIG.LEANCLOUD_MASTER_KEY
    leancloud.init(APP_ID, MASTER_KEY)

init()
