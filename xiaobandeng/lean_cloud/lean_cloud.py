from __future__ import absolute_import

import logging
from datetime import datetime

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
            self, fragment_order, start_at, end_at, media_id, fragment_src
    ):
        if fragment_order in self.fragments:
            return
        fragment = self.Fragment()
        fragment.set("media_id", media_id)
        fragment.set("fragment_order", fragment_order)
        fragment.set("start_at", start_at)
        fragment.set("end_at", end_at)
        fragment.set("fragment_src", fragment_src)
        self.fragments[fragment_order] = fragment

    def add_transcription_to_fragment(
            self, fragment_order, content, source_name
    ):
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

    def create_crowdsourcing_tasks(self):
        for fragment_order, fragment in self.fragments.iteritems():
            self.add_crowdsourcing_task(fragment.get("media_id"), fragment.id,
                                        fragment_order)
        if len(self.crowdsourcing_tasks) > 0:
            self.CrowdSourcingTask.save_all(self.crowdsourcing_tasks)

    def add_media(
            self,
            media_name,
            media_id,
            media_url,
            duration,
            company_name,
            requirement
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
        self.media = media

    def save(self):
        try:
            self.Fragment.save_all(self.fragments.values())

            relation = self.media.relation("containedTranscripts")
            for fragment in self.fragments.values():
                relation.add(fragment)
            self.media.save()

            print "transcript and media saved to lean cloud"
        except leancloud.LeanCloudError as e:
            print e
            raise

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

    def add_task(self, media_object_id, order, start_at, end_at, task_name):
        task = self.EditorTask()
        task.set("media_object_id", media_object_id)
        task.set("task_order", order)
        task.set("start_at", start_at)
        task.set("end_at", end_at)
        task.set("name", task_name)
        self.tasks.append(task)

    def get_fragment_by_start_at(self, start_at):
        self.fragment_query.greater_than_or_equal_to("start_at", start_at)
        self.fragment_query.limit(1)
        return self.fragment_query.find()

    def save_tasks(self):
        try:
            leancloud.Object.save_all(self.tasks)
        except Exception as e:
            print e.error
            print e.code
            raise
