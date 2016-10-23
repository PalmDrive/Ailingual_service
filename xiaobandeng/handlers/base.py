# -*- coding: utf-8 -*-

from __future__ import absolute_import

import logging

import tornado.httpclient
import tornado.httpserver
import tornado.ioloop
import tornado.web

import psutil
from ..lean_cloud.quota import get_quota
from ..lean_cloud.quota import update_access_count
from ..lean_cloud.user import UserMgr
from ..task.task import current_pending_tasks


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
        self.user_mgr = UserMgr()
        app_id = self.request.headers.get("app_id", "")
        app_key = self.request.headers.get("app_key", "")
        # return (true_or_false,user)
        if app_id and app_key:
            status, error_dict = self.user_mgr.login(app_id, app_key)
            if status:
                return (True, '')
            else:
                return (False,
                        self.response_error(error_dict.get("code"), "The app_id and app_key mismatch.")
                        )
        else:
            return (
                False,
                self.response_error(1001, "The app_id or app_key is not found in HTTP headers.")
            )

    def access_control(self, app_id):
        # check system cpu & mem
        if psutil.cpu_percent() > 90:
            return False

        if psutil.virtual_memory().percent() > 90:
            return False

        # pending tasks
        if current_pending_tasks() > 1000:
            return False

        # access quota
        try:
            count, quota = get_quota(app_id)
            if count > quota - 1:
                return False
        except Exception as e:
            logging.error(e)
            return False

        update_access_count(app_id)
        return True


    def response_error(self, code, error):
        data = {
            "status": "failure",
            "error": {
                "code": str(code),
                "message": "%s" % error
            }
        }

        return data

    def response_success(self):
        data = {
            "status": "success",
        }

        return data