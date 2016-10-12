# coding:utf-8

import leancloud
from datetime import datetime
from env_config import CONFIG
import traceback, sys

# singleton instance
class UserMgr(object):
    _instance = None

    def __new__(cls):
        if UserMgr._instance:
            return UserMgr._instance
        else:
            instance = object.__new__(cls)
            UserMgr._instance = instance
            return UserMgr._instance

    def __init__(self):

        APP_ID = CONFIG.LEANCLOUD_APP_ID
        MASTER_KEY = CONFIG.LEANCLOUD_MASTER_KEY
        leancloud.init(APP_ID, MASTER_KEY)
        self.User = leancloud.User

    def create_user(self, username, passwd):
        user = self.User()
        user.set_username(username)
        user.set_password(passwd)

        try:
            user.sign_up()
            res = (True, user)
        except leancloud.LeanCloudError as e:
            res = (False, e)

        return res

    def login(self, username, passwd):
        try:
            self.User().login(username, passwd)
            res = True, self.User.get_current()
        except leancloud.LeanCloudError as e:
            res = False, e

        return res


if __name__ == "__main__":
    import os
    import json
    import env_config
    import argparse

    pwd = os.path.dirname(__file__)
    env = 'develop'
    config_file = os.path.join(pwd, "config", env + ".json")
    config_dict = json.load(open(config_file))
    env_config.init_config(config_dict)

    parser = argparse.ArgumentParser()
    parser.add_argument('create_company',
                        help='create a company with random appid and appkey',
                        type=bool,
                        default=False
                        )

    args = parser.parse_args()
    user_mgr = UserMgr()

    if args.create_company:


    # print user_mgr.create_user('hello1', 'world')

#    print user_mgr.login('hello', 'world')
 #   print user_mgr.User.get_current()

    print 'over.'