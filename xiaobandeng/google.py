# coding=utf8
from __future__ import absolute_import

import argparse
import base64
import json
from multiprocessing import mp

from googleapiclient import discovery
import httplib2
from oauth2client.client import GoogleCredentials
from task import Task, TaskGroup

DISCOVERY_URL = ('https://{api}.googleapis.com/$discovery/rest?'
                 'version={apiVersion}')


class GoogleASR(object):
# Application default credentials provided by env variable
# GOOGLE_APPLICATION_CREDENTIALS
    def __init__(self):
        self.auth_ur = 'https://www.googleapis.com/auth/cloud-platform'
        credentials = GoogleCredentials.get_application_default().create_scoped(
            [self.auth_url])
        http = httplib2.Http()
        credentials.authorize(http)

        self.service = discovery.build(
            'speech', 'v1beta1', http=http, discoveryServiceUrl=DISCOVERY_URL)

        self.lanCodes = {'zh' : 'cmn-Hans-CN', 'en' : 'en-US'}

    def vop(self, filename, lan='zh'):
        print 'start google vop - ', filename

        lanCode = self.lanCodes[lan]

        with open(filename, 'rb') as speech:
            # Base64 encode the binary audio file for inclusion in the JSON
            # request.
            speech_content = base64.b64encode(speech.read())

        service_request = self.service.speech().syncrecognize(
            body={
                'config': {
                    # There are a bunch of config options you can specify. See
                    # https://goo.gl/KPZn97 for the full list.
                    'encoding': 'LINEAR16',  # raw 16-bit signed LE samples
                    'sampleRate': 16000,  # 16 khz
                    # See https://goo.gl/A9KJ1A for a list of supported languages.
                    'languageCode': lanCode,  # a BCP-47 language tag
                },
                'audio': {
                    'content': speech_content.decode('UTF-8')
                }
            })
        response = service_request.execute()
        return response

    def batch_vop(self, file_list, callback, starts, lan):
        num_workers = mp.cpu_count()
        pool = mp.Pool(num_workers)
        task_list = TaskGroup(file_list, lan, callback, starts)
        task_list.set_task_type(TaskBaidu, self.access_token)
        task_list.start()
        print datetime.datetime.now()

class TaskGoogle(Task):

    lans = {"zh": ['zh', 'zh', 'zh', 'en', 'en', 'en'],
            "en": ['en', 'en', 'en', 'zh', 'zh', 'zh']
            }

    def __init__(self, tid, file_name, pool, lan='zh', service=None):
        super(TaskGoogle, self).__init__(tid, file_name)
        self.service = service
        self.max_try = 6
        self._try = 0
        self.lan = lan
        self.url = self.get_url(lan)
        self.pool = pool

    def start(self):
        print 'start google vop on %s' % self.file_name
        res = self.pool.apply_async(self.service.vop, (self.file_name, self.lan))
        self.callback(res.get())

    def retry(self):
        self._try += 1
        if self._try < self.max_try:
            self.fetch(self.get_url(self.lans[self.lan][self._try]))
            print 'retry %s' % (self.id)
        else:
            self.complete()
            self.result = ''

    def callback(self, res):
        if len(res['results']) > 0:
            self.result = res['results'][0]['alternatives'][0]['transcript']
        else:
            # handle error
            self.result = 'Google API error: %s' % (json.dump(res))
        self.complete()

def main(speech_file):
    """Transcribe the given audio file.

    Args:
        speech_file: the name of the audio file.
    """
    g = GoogleASR()
    response = g.vop(speech_file, lan='zh')
    print(json.dumps(response))
    print(response['results'][0]['alternatives'][0]['transcript'])

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'speech_file', help='Full path of audio file to be recognized')
    args = parser.parse_args()
    main(args.speech_file)
