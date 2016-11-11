# coding:utf8

from task import Task

class SummarizationTask(Task):
    def __init__(
        self,
        title,
        content,
        order=None,
        completion_callback=None
    ):
        super(SummarizationTask, self).__init__(completion_callback)
        self.title = title
        self.content = content
        self.order = order

    def source_name(self):
        pass