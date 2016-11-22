# coding:u8
from ..base import BaseHandler
from ..error_code import ECODE
import leancloud
from xiaobandeng.lean_cloud.user import UserMgr

class SetAppInfoHandler(BaseHandler):
    def post(self, *args, **kwargs):
        client_id = self.get_argument("client_id")
        App = leancloud.Object.extend("App")
        app_query = App.query
        app_query.equal_to("objectId", client_id)
        user = app_query.find()

        if not user:
            self.write(self.response_error(*ECODE.ERR_USER_NO_THAT_USER))
            self.finish()
            return
        else:
            user = user[0]
        if user.get("appId"):
            self.write(self.response_error(*ECODE.ERR_USER_HAVE_APP_INFO))
            self.finish()
            return
        print user,'----'
        mgr = UserMgr()
        app_info = mgr.create_app_info()
        user.set("appId", app_info[0])
        user.set("appKey", app_info[1])
        user.save()

        self.write(self.response_success())