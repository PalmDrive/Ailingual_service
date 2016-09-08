import leancloud

APP_ID = 'hwB46P8KvcGH258ka0JfnMww-gzGzoHsz'
MASTER_KEY = 'ywhqmYxpFKTyemJrFl8YYT2j'


class LeanCloud(object):
    def __init__(self, audio_id):
        leancloud.init(APP_ID, MASTER_KEY)
        self.Fragment = leancloud.Object.extend(audio_id)
        self.fragments = []

    def add(self, fragment_id, start_at, end_at, content):
        fragment = self.Fragment()
        fragment.set('start_at', start_at)
        fragment.set('end_at', end_at)
        fragment.set('context', content)

        self.fragments.append(fragment)

    def upload(self):
        try:
            self.Fragment.save_all(self.fragments)
        except leancloud.LeanCloudError as e:
            print e
            raise
