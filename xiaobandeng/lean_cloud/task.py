# coding:utf-8
from __future__ import absolute_import

import datetime
import leancloud


CLASS_NAME_EDITORTASK = "EditorTask"


class LcTask(object):
    def __init__(self):
        self.EditorTask = leancloud.Object.extend(CLASS_NAME_EDITORTASK)
        self.editor_task_query = self.EditorTask.query
        self.tasks = []

    def batch_set_uid(self, task_id_list, uoid):
        # self.editor_task_query.do_cloud_query(
        # "select * from %s where objectId in (%s)" % (
        # CLASS_NAME_EDITORTASK,
        #         ','.join(["\"%s\"" % id for id in task_id_list])))
        self.editor_task_query.contained_in("objectId", task_id_list)

        result = self.editor_task_query.find()

        if result:
            for obj in result:
                obj.set("user_object_id", leancloud.User.create_without_data(uoid))
                obj.set("assign_at", datetime.datetime.now())
                obj.save()

            # self.EditorTask.save_all(result)

        return result
