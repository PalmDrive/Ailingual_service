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
        self.user_query = self.User.query
        self.company = None

    def get_user(self, uid):
        try:
            user = self.user_query.get(uid)
            return user
        except leancloud.LeanCloudError as e:
            if e.code ==101:
                return None

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

    def create_app_info(self):
        c_uuid = str(uuid.uuid1())
        return c_uuid[:23], c_uuid[24:]

    def create_company(self, company_name, username, password):
        user = self.User()
        c_uuid = self.create_app_info()

        user.set('company_name', company_name)
        user.set('app_id', c_uuid[0])
        user.set('app_key', c_uuid[1])

        user.set('username', username)
        user.set('password', password)

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

    def set_current_user(self, user):
        self.current_user = user
        self.roles = None

    def get_current_roles(self):
        if self.roles:
            return self.roles

        role_query = leancloud.Query(leancloud.Role)
        role_query.equal_to('users', self.current_user)
        role_query_list = role_query.find()  # 返回当前用户的角色列表
        self.roles = [role.get("name") for role in role_query_list]
        return self.roles

    def is_admin(self):
        return 'admin' in self.get_current_roles()

    def is_editor(self):
        return 'editor' in self.get_current_roles()

    def is_client(self):
        return 'company' in self.get_current_roles()
