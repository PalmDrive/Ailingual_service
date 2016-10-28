# coding:u8
from ..base import BaseHandler
from xiaobandeng.lean_cloud.user import UserMgr
from xiaobandeng.lean_cloud import lean_cloud

class CreateEditorTaskHandler(BaseHandler):
    def get(self, media_id):
        self.media_id = media_id

        self.lc = lean_cloud.LeanCloud()
        self.media = self.lc.get_media(self.media_id)
        task_duration = 10 * 60
        start_time = 0
        task_order = 0

        while True:
            fragment = self.lc.get_fragment_by_start_at(
                start_time + task_duration)
            if fragment:
                fragment = fragment[0]
                self.add_task(task_order, start_time, fragment.get("start_at"))
            else:
                self.add_task(task_order, start_time,
                              self.media.get("duration"))
                break
            start_time = fragment.get("start_at")
            task_order += 1

        self.lc.save_tasks()
        self.write(self.response_success())

    def add_task(self, order, start_at, end_at):
        self.lc.add_task(self.media, order, start_at, end_at,
                         self.media.get("media_name") + "-" + str(order), )


class AddUserTaskCountHandler(BaseHandler):
    def get(self):

        uid = self.get_argument("uid")
        diff_count = int(self.get_argument("task_count", 0))
        user_mgr = UserMgr()
        query = user_mgr.User.query
        user = query.get(uid)
        task_count = user.get("task_count", 0)
        task_count += diff_count
        if task_count < 0:
            task_count = 0

        user.set("task_count",task_count)
        user.save()
        self.write("success")