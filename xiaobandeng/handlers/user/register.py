# coding:u8
from ..base import BaseHandler
from ..error_code import ECODE
import leancloud
from xiaobandeng.lean_cloud.user import UserMgr

class SetAppInfoHandler(BaseHandler):
    def post(self, *args, **kwargs):
        client_id = self.get_argument("client_id")

        Company = leancloud.Object.extend("Company")
        App = leancloud.Object.extend("App")
        company_query = Company.query
        company_query.equal_to("objectId", client_id)
        company = company_query.find()

        if not company:
            self.write(self.response_error(*ECODE.ERR_COMPANY_NO_THAT_COMPANY))
            self.finish()
            return
        else:
            company = company[0]

        app = App()


        mgr = UserMgr()
        app_info = mgr.create_app_info()
        app.set("appId", app_info[0])
        app.set("appKey", app_info[1])

        app.set("client",company)
        app.save()

        self.write(self.response_success())