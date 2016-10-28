# coding:u8
from ..base import BaseHandler
from xiaobandeng.lean_cloud.user import UserMgr
from ..error_code import ECODE


class SetAppInfoHandler(BaseHandler):
    def post(self, *args, **kwargs):
        uid = self.get_argument("uid")
        mgr = UserMgr()
        user = mgr.get_user(uid)
        if not user:
            self.write(self.response_error(*ECODE.ERR_USER_NO_THAT_USER))
            self.finish()
            return
        if user.get("app_id"):
            self.write(self.response_error(*ECODE.ERR_USER_HAVE_APP_INFO))
            self.finish()
            return
        app_info = mgr.create_app_info()
        user.set("app_id", app_info[0])
        user.set("app_key", app_info[1])
        user.save()

        self.write(self.response_success())