from __future__ import absolute_import
import leancloud

CLASS_NAME_TEXT_ANALYSIS = "TextAnalysis"
CLASS_NAME_COMPANY = "Company"

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

        Company = leancloud.Object.extend(CLASS_NAME_COMPANY)
        client = Company.create_without_data(client_id)
        text_analysis.set("client", client)

        self.text_analysis = text_analysis

    def save(self):
        self.text_analysis.save()
        return  self.text_analysis.id



