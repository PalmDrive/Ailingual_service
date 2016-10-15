# -*- coding: utf-8 -*-

from __future__ import absolute_import

import psutil
from xiaobandeng.lean_cloud.quota import get_quota
from xiaobandeng.lean_cloud.quota import update_access_count

import tornado.httpclient
import tornado.httpserver
import tornado.ioloop
import tornado.web
from xiaobandeng.lean_cloud.user import UserMgr


class BaseHandler(tornado.web.RequestHandler):
    def prepare(self):
        # set access control allow_origin
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers",
                        "X-Requested-With, Content-Type,"
                        "x-smartchat-key,client-source")
        self.set_header("Access-Control-Allow-Methods",
                        "PUT,POST,GET,DELETE,OPTIONS")
        # 如果CORS请求将withCredentials标志设置为true，使得Cookies可以随着请求发送。
        # 如果服务器端的响应中,没有返回Access-Control-Allow-Credentials: true的响应头，
        # 那么浏览器将不会把响应结果传递给发出请求的脚本程序.

        # 给一个带有withCredentials的请求发送响应的时候,
        # 服务器端必须指定允许请求的域名,不能使用"*".否则无效
        # self.set_header("Access-Control-Allow-Credentials", "true")

    def options(self):
        self.set_header("Allow", "GET,HEAD,POST,PUT,DELETE,OPTIONS")

    def check_company_user(self):
        user_mgr = UserMgr()
        app_id = self.request.headers.get("app_id", "")
        app_key = self.request.headers.get("app_key", "")
        # return (true_or_false,user)
        if app_id and app_key:
            return user_mgr.login(app_id, app_key)
        else:
            return (
                False, Exception("app_id or app_key not found in http headers")
            )


    def access_control(self, app_id):
        # check system cpu & mem
        if psutil.cpu_percent() > 90:
            return False

        if psutil.virtual_memory().percent() > 90:
            return False

        try:
            count, quota = get_quota(app_id)
            if count > quota - 1:
                return False
        except Exception as e:
            logging.error(e)
            return False

        update_access_count(app_id)
        return True