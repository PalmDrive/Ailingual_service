# coding:utf-8
from __future__ import absolute_import

import uuid

import leancloud


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

    def create_company(self, company_name):
        user = self.User()
        c_uuid = str(uuid.uuid1())

        user.set('company_name', company_name)
        user.set('app_id', c_uuid[:23])
        user.set('app_key', c_uuid[24:])

        user.set('username', c_uuid[:23])
        user.set('password', c_uuid[24:])

        try:
            user.sign_up()
            res = (True, user)
        except leancloud.LeanCloudError as e:
            res = (False, e)

        return res

    def login(self, username, passwd):
        try:
            self.User().login(username, passwd)
            # this api didn't return user.
            res = True, ''
        except leancloud.LeanCloudError as e:
            # use e.error,e.code to get error message
            res = False, {"code": e.code, "error": e.error}
        return res
