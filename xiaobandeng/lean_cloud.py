import leancloud
import datetime

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

    def add_fragment(self, fragment_order, start_at, end_at, content, media_name,
            media_id, media_src):
        fragment = self.Fragment()
        fragment.set('media_id', media_id)
        fragment.set('media_name', media_name)
        fragment.set('fragment_order', fragment_order)
        fragment.set('start_at', start_at)
        fragment.set('end_at', end_at)
        fragment.set('content', content)
        fragment.set('media_src', media_src)
        self.fragments.append(fragment)

    def add_media(self, media_name, media_id, media_url, duration):
        media = self.Media()
        media.set('media_id', media_id)
        media.set('media_name', media_name)
        media.set('media_url', media_url)
        media.set('duration', duration)
        media.set('company_name', duration)
        media.set('received_at', duration)
        media.set('transcribed_at', datetime.datetime())
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