import leancloud

APP_ID = 'hwB46P8KvcGH258ka0JfnMww-gzGzoHsz'
MASTER_KEY = 'ywhqmYxpFKTyemJrFl8YYT2j'
CLASS_NAME = 'Transcript'


class LeanCloud(object):
    def __init__(self):
        leancloud.init(APP_ID, MASTER_KEY)
        self.Fragment = leancloud.Object.extend(CLASS_NAME)
        self.fragments = []

    def add(self, fragment_order, start_at, end_at, content, course_name):
        fragment = self.Fragment()
        fragment.set('fragment_order', fragment_order)
        fragment.set('start_at', start_at)
        fragment.set('end_at', end_at)
        fragment.set('content', content)
        fragment.set('course_name', course_name)
        self.fragments.append(fragment)

    def upload(self):
        try:
            self.Fragment.save_all(self.fragments)
        except leancloud.LeanCloudError as e:
            print e
            raise
