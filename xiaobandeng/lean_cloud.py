import leancloud

APP_ID = 'hwB46P8KvcGH258ka0JfnMww-gzGzoHsz'
MASTER_KEY = 'ywhqmYxpFKTyemJrFl8YYT2j'
CLASS_NAME = 'Transcript'


class LeanCloud(object):
    def __init__(self):
        leancloud.init(APP_ID, MASTER_KEY)
        self.Fragment = leancloud.Object.extend(CLASS_NAME)
        self.fragments = []

    def add(self, fragment_order, start_at, end_at, content, media_name, media_id):
        fragment = self.Fragment()
        fragment.set('media_id', media_id)
        fragment.set('media_name', media_name)
        fragment.set('fragment_order', fragment_order)
        fragment.set('start_at', start_at)
        fragment.set('end_at', end_at)
        fragment.set('content', content)
        self.fragments.append(fragment)

    def upload(self):
        try:
            self.Fragment.save_all(self.fragments)
        except leancloud.LeanCloudError as e:
            print e
            raise
