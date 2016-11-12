from __future__ import absolute_import

import logging
from datetime import datetime
from xiaobandeng.handlers import constants
import leancloud

CLASS_NAME_TRANSCRIPT = "Transcript"
CLASS_NAME_MEDIA = "Media"
CLASS_NAME_CROWDSOURCINGTASK = "CrowdsourcingTask"
CLASS_NAME_EDITORTASK = "EditorTask"


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
            set_type="machine"
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

        self.fragments[fragment_order] = fragment

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
            company_name,
            requirement,
            language,
            service_provider,
            transcript_sets=None,
    ):
        media = self.Media()
        media.set("media_id", media_id)
        media.set("media_name", media_name)
        media.set("media_src", media_url)
        media.set("duration", duration)
        media.set("company_name", company_name)
        media.set("transcribed_at", datetime.now())
        media.set("status", "Auto Transcribed")
        media.set("requirement", requirement)
        media.set("assign_status", constants.LC_MEDIA_ASSIGN_STATUS_NONE)
        media.set("completion_status", 0)
        media.set("lan", language)

        if not service_provider:
            service_provider = []
        media.set("service_providers", service_provider)

        if not transcript_sets:
            media.set("transcript_sets", {"machine": 1})

        self.media = media
        print 'added_media_id:%s' % media_id

    def save(self):
        # try:
        # batch save all fragments
        self.Fragment.save_all(self.fragments.values())

        relation = self.media.relation("containedTranscripts")
        for fragment in self.fragments.values():
            relation.add(fragment)
        # save media
        self.media.save()
        # print "transcript and media saved to lean cloud"
        # except leancloud.LeanCloudError as e:
        # print e
        # raise

    def batch_update_fragment_url(self):
        fragments = []
        for fragment in self.fragments.values():
            if fragment.get("fragment_src"):
                fragments.append(fragment)
        if fragments:
            # try:
            # self.Fragment.save_all(fragments)
            for i in fragments:
                i.save()
                # except Exception as e:
                # print e.code
                # print e.error
                # print '--------------'
                # print 'updated fragments url'

    def get_list(self, media_id):
        total_data = []

        def batch_fetch(start):
            query = self.fragment_query.equal_to("media_id", media_id)
            query.add_ascending("start_at")

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
