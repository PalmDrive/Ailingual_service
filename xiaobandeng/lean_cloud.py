import leancloud

APP_ID = 'hwB46P8KvcGH258ka0JfnMww-gzGzoHsz'
MASTER_KEY = 'ywhqmYxpFKTyemJrFl8YYT2j'
CLASS_NAME = 'Transcript'


class LeanCloud(object):
    def __init__(self):
        leancloud.init(APP_ID, MASTER_KEY)
        self.Fragment = leancloud.Object.extend(CLASS_NAME)
        self.fragments = []
        self.fragment_query = self.Fragment.query

    def add(self, fragment_order, start_at, end_at, content, media_name,
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

    def upload(self):
        try:
            self.Fragment.save_all(self.fragments)
        except leancloud.LeanCloudError as e:
            print e
            raise

    def get_list(self, media_id, order_by='fragment_order'):
        query = self.fragment_query.equal_to('media_id', media_id)
        query.add_ascending(order_by)
        return query.find()