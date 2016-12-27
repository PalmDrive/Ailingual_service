# coding:utf8
from __future__ import absolute_import

import logging
from datetime import datetime
from xiaobandeng.handlers import constants
import leancloud

CLASS_NAME_TRANSCRIPT = "Transcript"
CLASS_NAME_MEDIA = "Media"
CLASS_NAME_CROWDSOURCINGTASK = "CrowdsourcingTask"
CLASS_NAME_EDITORTASK = "EditorTask"
CLASS_NAME_COMPANY = "Company"


class LeanCloud(object):
    def __init__(self):
        self.Fragment = leancloud.Object.extend(CLASS_NAME_TRANSCRIPT)
        self.fragments = {}
        self.fragment_query = self.Fragment.query

        self.Media = leancloud.Object.extend(CLASS_NAME_MEDIA)
        self.media_query = self.Media.query
        self.media = None

        self.CrowdSourcingTask = leancloud.Object.extend(
            CLASS_NAME_CROWDSOURCINGTASK)
        self.crowdsourcing_tasks = []

        self.EditorTask = leancloud.Object.extend(CLASS_NAME_EDITORTASK)
        self.editor_task_query = self.EditorTask.query
        self.tasks = []

    def set_fragment(
            self, fragment_order, start_at, end_at, media_id, fragment_src,
            set_type="machine", task_id=""
    ):
        if fragment_order in self.fragments:
            return

        fragment = self.Fragment()
        fragment.set("media_id", media_id)
        fragment.set("fragment_order", fragment_order)
        fragment.set("start_at", start_at)
        fragment.set("end_at", end_at)
        fragment.set("fragment_src", fragment_src)
        fragment.set("set_type", set_type)
        fragment.set("task_id", task_id)

        self.fragments[fragment_order] = fragment
        return fragment

    def set_fragment_src(self, fragment, src):
        fragment.set("fragment_src", src)

    def add_transcription_to_fragment(
            self, fragment_order, content, source_name
    ):
        # this fragment_order is the task_order
        # is the task index in task_group.tasks

        fragment = self.fragments[fragment_order]
        if fragment:
            key = "content_" + source_name
            content_array = fragment.get(key)
            if content_array is None:
                content_array = []
            content_array.append(content)
            fragment.set(key, content_array)

    def add_crowdsourcing_task(
            self, media_id, fragment_id, fragment_order
    ):
        crowdsourcing_task = self.CrowdSourcingTask()
        crowdsourcing_task.set("media_id", media_id)
        crowdsourcing_task.set("fragment_id", fragment_id)
        crowdsourcing_task.set("fragment_order", fragment_order)
        crowdsourcing_task.set("status", 0)
        crowdsourcing_task.set("fragment_type", "Transcript")
        self.crowdsourcing_tasks.append(crowdsourcing_task)

    def batch_create_crowdsourcing_tasks(self, task_group):
        for fragment_order, fragment in self.fragments.iteritems():
            if task_group.tasks[fragment_order].on_oss:
                self.add_crowdsourcing_task(fragment.get("media_id"),
                                            fragment.id,
                                            fragment_order)
            else:
                print "warnx:\n media id:%s, fragment no url fragment order is:%s" % (
                    self.media.get("media_id"), fragment_order)
        if len(self.crowdsourcing_tasks) > 0:
            self.CrowdSourcingTask.save_all(self.crowdsourcing_tasks)

    def add_media(
            self,
            media_name,
            media_id,
            media_url,
            duration,
            creater_id,
            client_id,
            requirement,
            language,
            service_provider,
            transcript_sets,
            caption_type,
            fields
    ):
        media = self.Media()
        media.set("media_id", media_id)
        media.set("media_name", media_name)
        media.set("media_src", media_url)
        media.set("duration", duration)

        Company = leancloud.Object.extend(CLASS_NAME_COMPANY)

        creater = Company.create_without_data(creater_id)
        media.set("creater", creater)
        if client_id:
            client = Company.create_without_data(client_id)
            media.set("client", client)

        media.set("transcribed_at", datetime.now())
        media.set("status", "Auto Transcribed")
        media.set("requirement", requirement)
        media.set("assign_status", constants.LC_MEDIA_ASSIGN_STATUS_NONE)
        media.set("completion_status", 0)
        media.set("lan", language)
        media.set("transcribe_status", 0)
        media.set("fields", fields)

        if not service_provider:
            service_provider = []
        media.set("service_providers", service_provider)

        if not transcript_sets:
            media.set("transcript_sets", {"machine": 1})

        media.set("caption_type", caption_type)

        self.media = media
        print 'added_media_id:%s' % media_id

    def save_fragments(self):
        self.Fragment.save_all(self.fragments.values())

    def save_media(self):
        self.media.save()

    def set_duration(self, duration):
        self.media.set("duration", duration)
        self.media.save()

    def set_transcribe_status(self, status):
        self.media.set("transcribe_status", status)
        self.media.save()

    def get_timeline_task(self, proof_task_id):
        '''
        获取 timeline 指定类型的 任务
        :param task_id: 校对任务 id
        :return:
        '''
        self.editor_task_query = self.EditorTask.query

        self.editor_task_query.equal_to("proof_task_id", proof_task_id)
        task_list = self.editor_task_query.find()
        if task_list:
            return task_list[0]
        else:
            return None

    def get_editor_task(self, task_id):
        '''
        :param task_id: 任务 id
        :return:
        '''
        self.editor_task_query = self.EditorTask.query

        self.editor_task_query.equal_to("objectId", task_id)
        task_list = self.editor_task_query.find()
        if task_list:
            return task_list[0]
        else:
            return None

    def save(self):
        self.save_fragments()

        values = self.fragments.values()
        save_count = len(values) / 800

        for i in range(save_count + 1):
            relation = self.media.relation("containedTranscripts")
            for fragment in values[slice(i * 800, (i + 1) * 800)]:
                relation.add(fragment)
            self.media.save()

    def batch_update_fragment_url(self):
        fragments = []
        for fragment in self.fragments.values():
            if fragment.get("fragment_src"):
                fragments.append(fragment)
        if fragments:
            for i in fragments:
                i.save()

    def get_list(self, media_id, set_type="machine"):
        total_data = []

        def batch_fetch(start):
            query = self.fragment_query.equal_to("media_id", media_id)
            query.add_ascending("start_at")
            query.equal_to("set_type", set_type)

            if start:
                start_at = start.get("start_at")
            else:
                start_at = 0

            query.greater_than("start_at", start_at)
            query.limit(800)
            result = query.find()
            total_data.extend(result)

            if len(result) == 800:
                start = result[-1]
                batch_fetch(start)
            else:
                return

        batch_fetch(0)

        logging.info("fetched :%s" % len(total_data))
        return total_data

    def get_transcript_list_by_timeline_task(self, timeline_task,
                                             set_type="machine"):
        total_data = []
        media_id = timeline_task.get("media_id")
        task_start_at = timeline_task.get("start_at")
        task_end_at = timeline_task.get("end_at")

        def batch_fetch(start):
            query = self.fragment_query.equal_to("media_id", media_id)
            query.add_ascending("start_at")
            query.equal_to("set_type", set_type)

            query.greater_than_or_equal_to("start_at", task_start_at)
            query.less_than_or_equal_to("start_at", task_end_at)

            if start:
                start_at = start.get("start_at")
            else:
                start_at = 0

            query.greater_than("start_at", start_at)
            query.limit(800)
            result = query.find()
            total_data.extend(result)

            if len(result) == 800:
                start = result[-1]
                batch_fetch(start)
            else:
                return

        batch_fetch(0)

        logging.info("fetched :%s" % len(total_data))
        return total_data

    def get_media(self, media_id):
        query = self.media_query.equal_to("media_id", media_id)
        return query.first()

    def get_media_list_by_media_id(self, media_id_list):
        self.media_query.contained_in("media_id", media_id_list)

        return self.media_query.find()


    def add_task(self, media_object, order, start_at, end_at, task_name,
                 task_type):
        task = self.EditorTask()
        task.set("media_id", media_object.get("media_id"))
        task.set("media_object_id", media_object)
        task.set("task_order", order)
        task.set("start_at", start_at)
        task.set("end_at", end_at)
        task.set("name", task_name)
        task.set("task_type", task_type)
        self.tasks.append(task)
        return task

    def get_fragment_by_start_at(self, media_id, start_at):
        self.fragment_query.greater_than_or_equal_to("start_at", start_at)
        self.fragment_query.add_ascending("start_at")
        self.fragment_query.equal_to("media_id", media_id)
        self.fragment_query.limit(1)
        return self.fragment_query.find()

    def get_last_fragment_by_end_at(self, media_id):
        self.fragment_query.equal_to("media_id", media_id)
        self.fragment_query.add_descending("end_at")
        self.fragment_query.limit(1)
        return self.fragment_query.find()

    def save_tasks(self):
        try:
            leancloud.Object.save_all(self.tasks)
        except Exception as e:
            print e.error
            print e.code
            raise
