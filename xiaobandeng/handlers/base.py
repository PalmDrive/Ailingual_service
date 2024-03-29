# -*- coding: utf-8 -*-

from __future__ import absolute_import

import logging
import psutil

import tornado.httpclient
import tornado.httpserver
import tornado.ioloop
import tornado.web

from .error_code import ECODE
from ..lean_cloud.quota import get_quota
from ..lean_cloud.quota import update_access_count
from ..lean_cloud.session import SessionMgr
from ..task.task import current_pending_tasks


class BaseHandler(tornado.web.RequestHandler):
    def prepare(self):
        # set access control allow_origin
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers",
                        "X-Requested-With, Content-Type,"
                        "x-ailingual-key,client-source,"
                        "app_id,app_key")
        self.set_header("Access-Control-Allow-Methods",
                        "PUT,POST,GET,DELETE,OPTIONS")
        # 如果CORS请求将withCredentials标志设置为true，使得Cookies可以随着请求发送。
        # 如果服务器端的响应中,没有返回Access-Control-Allow-Credentials: true的响应头，
        # 那么浏览器将不会把响应结果传递给发出请求的脚本程序.

        # 给一个带有withCredentials的请求发送响应的时候,
        # 服务器端必须指定允许请求的域名,不能使用"*".否则无效
        # self.set_header("Access-Control-Allow-Credentials", "true")

    def options(self, *args, **kwargs):
        self.set_header("Allow", "GET,HEAD,POST,PUT,DELETE,OPTIONS")
        self.finish()
        return
    def authenticate(self):
        self.session_manager = SessionMgr()
        app_id = self.request.headers.get("app_id", "")
        app_key = self.request.headers.get("app_key", "")

        if app_id and app_key:
            result = self.session_manager.authenticate(app_id, app_key)
            if result:
                return (True, '')
            else:
                return (False,
                        self.response_error(*ECODE.ERR_USER_APP_ID_APP_KEY_NOT_MATCH)
                        )

        return (False,
                self.response_error(*ECODE.ERR_USER_NO_THAT_APP_INFO)
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


    def response_error(self, code, error,body={}):
        data = {
            "status": "failure",
            "error": {
                "code": str(code),
                "message": "%s" % error
            }
        }

        data["error"].update(body)
        return data

    def response_success(self, _append={}):
        data = {
            "status": "success",
        }
        data.update(_append)

        return data