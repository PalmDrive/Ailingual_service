from __future__ import absolute_import
import leancloud

CLASS_NAME_TEXT_ANALYSIS = "TextAnalysis"

class LeanCloudSummarize(object):

    def __init__(self):
        self.TextAnalysis = leancloud.Object.extend(CLASS_NAME_TEXT_ANALYSIS)

    def add_summary(
            self, title, content, summary, client_id
    ):
        text_analysis = self.TextAnalysis()
        text_analysis.set("text", content)
        if title:
            text_analysis.set("title", title)
        text_analysis.set("summary", summary)
        text_analysis.set("clientId", client_id)
        self.text_analysis = text_analysis

    def save(self):
        self.text_analysis.save()
        return  self.text_analysis.id



