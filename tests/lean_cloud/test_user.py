from __future__ import absolute_import

from xiaobandeng.config import load_config
from xiaobandeng.lean_cloud.user import UserMgr
from xiaobandeng.lean_cloud import init
from xiaobandeng.config import CONFIG


def test_creation():
    env = 'develop'
    load_config(env)
    init(CONFIG)
    user_mgr = UserMgr()
    return user_mgr.create_company("test_company","test_company","abc123")

    # print user_mgr.create_user('hello1', 'world')

    # print user_mgr.login('hello', 'world')
    #   print user_mgr.User.get_current()

res,err = test_creation()
if err:
    print err
