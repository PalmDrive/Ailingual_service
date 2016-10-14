from __future__ import absolute_import

from xiaobandeng.config import load_config
from xiaobandeng.lean_cloud import init
from xiaobandeng.config import CONFIG
from xiaobandeng.lean_cloud.quota import get_quota, update_access_count


def test_creation():
    env = 'develop'
    load_config(env)
    init(CONFIG)
    x, y = get_quota("test_id")
    update_access_count("test_id")
    print x, y
