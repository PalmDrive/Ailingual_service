import leancloud
from datetime import datetime
from env_config import CONFIG

CLASS_NAME_TRANSCRIPT = 'Transcript'
CLASS_NAME_MEDIA = 'Media'

class LeanCloud(object):
    def __init__(self):
        APP_ID = CONFIG.LEANCLOUD_APP_ID
        MASTER_KEY = CONFIG.LEANCLOUD_MASTER_KEY

        leancloud.init(APP_ID, MASTER_KEY)
        self.Fragment = leancloud.Object.extend(CLASS_NAME_TRANSCRIPT)
        self.fragments = {}
        self.fragment_query = self.Fragment.query

        self.Media = leancloud.Object.extend(CLASS_NAME_MEDIA)
        self.media_query = self.Media.query

    def set_fragment(self, fragment_order, start_at, end_at,
            media_id, fragment_src):
        if fragment_order in self.fragments:
            return
        fragment = self.Fragment()
        fragment.set('media_id', media_id)
        fragment.set('fragment_order', fragment_order)
        fragment.set('start_at', start_at)
        fragment.set('end_at', end_at)
        fragment.set('fragment_src', fragment_src)
        self.fragments[fragment_order] = fragment

    def add_transcription_to_fragment(self, fragment_order, content, source_name):
        fragment = self.fragments[fragment_order]
        if fragment:
            key = 'content_' + source_name
            content_array = fragment.get(key)
            if content_array is None:
                content_array = []
            content_array.append(content)
            fragment.set(key, content_array)

    def add_media(self, media_name, media_id, media_url, duration, company_name):
        media = self.Media()
        media.set('media_id', media_id)
        media.set('media_name', media_name)
        media.set('media_src', media_url)
        media.set('duration', duration)
        media.set('company_name', company_name)
        media.set('transcribed_at', datetime.now())
        media.set('status', 'Auto Transcribed')
        self.media = media

    def save(self):
        try:
            self.Fragment.save_all(self.fragments.values())

            relation = self.media.relation('containedTranscripts')
            for fragment in self.fragments.values():
                relation.add(fragment)
            self.media.save()

            print 'transcript and media saved to lean cloud'
        except leancloud.LeanCloudError as e:
            print e
            raise

    def get_list(self, media_id, order_by='fragment_order'):
        query = self.fragment_query.equal_to('media_id', media_id)
        query.add_ascending(order_by)
        query.limit(1000)
        return query.find()

    def get_media(self,media_id):
        query = self.media_query.equal_to('media_id',media_id)
        return query.find()