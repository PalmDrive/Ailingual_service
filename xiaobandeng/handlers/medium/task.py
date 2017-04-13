# coding:u8
from ..base import BaseHandler
from xiaobandeng.lean_cloud.user import UserMgr
from xiaobandeng.lean_cloud import lean_cloud
from xiaobandeng.lean_cloud.task import LcTask
from xiaobandeng.handlers.error_code import ECODE
from collections import defaultdict
from xiaobandeng.handlers import constants
from xiaobandeng.lean_cloud.utils import loop_until_return


class EditorTask(object):
    def __init__(self, media_id):
        self.media_id = media_id

        self.lc = lean_cloud.LeanCloud()
        self.media = self.lc.get_media(self.media_id)

    def create(self):
        task_duration = 10 * 60
        start_time = 0
        task_order = 1

        self.copy_list = [u"内部校对1"]

        while True:
            fragment = loop_until_return(5, self.lc.get_fragment_by_start_at,
                                         self.media_id,
                                         start_time + task_duration)
            if fragment:
                fragment = fragment[0]
                for i in range(len(self.copy_list)):
                    self.add_task(task_order, start_time,
                                  fragment.get("start_at"), i)
            else:
                # have last fragment
                if fragment:
                    for i in range(len(self.copy_list)):
                        self.add_task(task_order, start_time,
                                      self.media.get("duration"), i)
                # is first fragment and <10min
                else:
                    for i in range(len(self.copy_list)):
                        self.add_task(task_order, start_time,
                                      self.media.get("duration"), i)
                break

            start_time = fragment.get("start_at")
            task_order += 1

        self.media.set("editor_task_count",
                       task_order * (len(self.copy_list)))

        self.media.save()
        self.lc.save_tasks()


    def add_task(self, order, start_at, end_at, task_type):
        self.lc.add_task(self.media, order, start_at, end_at,
                         self.media.get("media_name") + self.copy_list[
                             task_type] + u"{第" + str(
                             order) + u"段}", task_type)


class CreateEditorTaskHandler(BaseHandler):
    def get(self, media_id):
        EditorTask(media_id).create()
        self.write(self.response_success())


class CreateTimelineTaskHandler(BaseHandler):
    def post(self, media_id):
        self.media_id = media_id

        self.lc = lean_cloud.LeanCloud()
        self.media = self.lc.get_media(self.media_id)

        proof_task_id = self.get_body_argument("proof_task_id")
        timeline_task = self.lc.get_timeline_task(proof_task_id)
        if timeline_task:
            self.write(self.response_success())
            self.finish()
            return

        proof_task = self.lc.get_editor_task(proof_task_id)

        self.add_timeline_task(proof_task)
        self.write(self.response_success())

    def add_timeline_task(self, proof_task):
        """
        增加一个对轴类型任务
        :param proof_task: 校对任务
        :return: None
        """
        proof_task_id = proof_task.id
        order = proof_task.get("task_order")
        start_at = proof_task.get("start_at")
        end_at = proof_task.get("end_at")

        task = self.lc.add_task(self.media, order, start_at, end_at,
                                self.media.get(
                                    "media_name") + u"内部校对2" + u"{第" + str(
                                    order) + u"段}",
                                constants.TASK_TYPE_TIMELINE)  # task_type:对轴类型
        task.set("proof_task_id", proof_task_id)  # set proof task id
        task.save()


class BatchAssignUserHandler(BaseHandler):
    def post(self):
        uid = self.get_argument("uid")
        task_ids = self.get_argument("task_ids")
        task_id_list = task_ids.split(",")
        diff_count = len(task_id_list)
        media_task_map = defaultdict(list)

        lc_task = LcTask()
        task_list = lc_task.batch_set_uid(task_id_list, uid)

        for task in task_list:
            media_task_map[task.get("media_id")].append(task)

        lc = lean_cloud.LeanCloud()

        media_list = lc.get_media_list_by_media_id(media_task_map.keys())
        for media in media_list:
            task_count = media.get("editor_task_count")
            cur_task_count = int(media.get("assigned_editor_task", 0))
            cur_task_count += len(media_task_map[media.get("media_id")])

            if cur_task_count < task_count:
                media.set("assign_status",
                          constants.LC_MEDIA_ASSIGN_STATUS_PART)
            if cur_task_count == task_count:
                media.set("assign_status", constants.LC_MEDIA_ASSIGN_STATUS_ALL)

            media.set("assigned_editor_task", cur_task_count)
            media.save()

        # if media_list:
        # lc.Media.save_all()

        try:
            user_mgr = UserMgr()
            user = user_mgr.User.query.get(uid)
            task_count = user.get("task_count", 0)
            task_count += diff_count
            if task_count < 0:
                task_count = 0

            user.set("task_count", task_count)
            user.save()
            self.write(self.response_success())

        except lean_cloud.leancloud.LeanCloudError:
            self.write(self.response_error(*ECODE.ERR_USER_NO_THAT_USER))
            return



