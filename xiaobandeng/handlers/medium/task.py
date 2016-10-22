# coding:u8
from ..base import BaseHandler
from xiaobandeng.lean_cloud import lean_cloud

class EditorTaskHandler(BaseHandler):
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

    def add_task(self, order, start_at, end_at):
        self.lc.add_task(self.media_id, order, start_at, end_at,
                         self.media.get("media_name") + "-" + str(order))
