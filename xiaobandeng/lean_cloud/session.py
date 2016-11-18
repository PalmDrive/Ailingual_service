# coding:utf-8
from __future__ import absolute_import

import leancloud

CLASS_NAME_COMPANY = "Company"
CLASS_NAME_APP = "App"

class SessionMgr(object):

    def __init__(self):
        self.company = None
        self.App = leancloud.Object.extend(CLASS_NAME_APP)

    def authenticate(self, app_id, app_key):
        self.app_query = self.App.query
        self.app_query.equal_to("appId", app_id)
        self.app_query.equal_to("appKey", app_key)
        result = self.app_query.find()
        if result and len(result) > 0:
            self.app = result[0]
            self.company = self.app.get('client')
            return True
        else:
            return False

    def is_client_company(self):
        return self.company.get('role') == 'client'