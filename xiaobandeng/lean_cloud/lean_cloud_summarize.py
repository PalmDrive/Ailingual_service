from __future__ import absolute_import
import leancloud

CLASS_NAME_TEXT_ANALYSIS = "TextAnalysis"

class LeanCloudSummarize(object):

    def __init__(self):
        self.TextAnalysis = leancloud.Object.extend(CLASS_NAME_TEXT_ANALYSIS)
        self.text_analysis = self.TextAnalysis()

    def init_text_analyisis(
            self, title, content, client_id
    ):
        self.text_analysis.set("text", content)
        if title:
            self.text_analysis.set("title", title)

        text_analysis.set("clientId", client_id)

    def set_summary(self, summary):
        if summary:
            self.text_analysis.set("summary", summary)

    def save(self):
        self.text_analysis.save()
        return  self.text_analysis.id



