import leancloud
from datetime import datetime

APP_ID = 'hwB46P8KvcGH258ka0JfnMww-gzGzoHsz'
MASTER_KEY = 'ywhqmYxpFKTyemJrFl8YYT2j'
CLASS_NAME_TRANSCRIPT = 'Transcript'
CLASS_NAME_MEDIA = 'Media'

class LeanCloud(object):
    def __init__(self):
        leancloud.init(APP_ID, MASTER_KEY)
        self.Fragment = leancloud.Object.extend(CLASS_NAME_TRANSCRIPT)
        self.fragments = []
        self.fragment_query = self.Fragment.query

        self.Media = leancloud.Object.extend(CLASS_NAME_MEDIA)
        self.media = []

    def add_fragment(self, fragment_order, start_at, end_at, content,
            media_id):
        fragment = self.Fragment()
        fragment.set('media_id', media_id)
        fragment.set('fragment_order', fragment_order)
        fragment.set('start_at', start_at)
        fragment.set('end_at', end_at)
        fragment.set('content', content)
        self.fragments.append(fragment)

    def add_media(self, media_name, media_id, media_url, duration, company_name):
        media = self.Media()
        media.set('media_id', media_id)
        media.set('media_name', media_name)
        media.set('media_src', media_url)
        media.set('duration', duration)
        media.set('company_name', company_name)
        media.set('transcribed_at', datetime.now())
        media.set('status', 'Auto Transcribed')
        self.media.append(media)

    def upload(self):
        try:
            self.Fragment.save_all(self.fragments)
            self.Media.save_all(self.media)
        except leancloud.LeanCloudError as e:
            print e
            raise

    def get_list(self, media_id, order_by='fragment_order'):
        query = self.fragment_query.equal_to('media_id', media_id)
        query.add_ascending(order_by)
        query.limit(1000)
        return query.find()