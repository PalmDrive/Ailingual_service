# coding=utf8
from __future__ import absolute_import

import argparse
import base64
import json
import threading

from googleapiclient import discovery
import httplib2
from oauth2client.client import GoogleCredentials
from transcribe.task import TaskGroup, TranscriptionTask

DISCOVERY_URL = ('https://{api}.googleapis.com/$discovery/rest?'
                 'version={apiVersion}')

class TaskGoogle(TranscriptionTask):

    def __init__(self, service, file_name, start_time, order=None, lan='zh', completion_callback=None):
        super(TaskGoogle, self).__init__(file_name, start_time, order, lan, completion_callback)
        self.service = service
        self.lan = lan

    def source_name(self):
        return 'google'

    def start(self):
        threading.Thread(target=self.service.vop, args=(self.file_name, self.lan, self.callback,)).start()

    def callback(self, res):
        if len(res['results']) > 0:
            self.result = res['results'][0]['alternatives'][0]['transcript']
        else:
            # handle error
            self.result = 'Google API error: %s' % (json.dump(res))
        self.complete()

class GoogleASR(object):
# Application default credentials provided by env variable
# GOOGLE_APPLICATION_CREDENTIALS
    def __init__(self, pool = None):
        self.auth_url = 'https://www.googleapis.com/auth/cloud-platform'
        credentials = GoogleCredentials.get_application_default().create_scoped(
            [self.auth_url])
        http = httplib2.Http()
        credentials.authorize(http)

        self.service = discovery.build(
            'speech', 'v1beta1', http=http, discoveryServiceUrl=DISCOVERY_URL)

        self.lanCodes = {'zh' : 'cmn-Hans-CN',
                         'en' : 'en-US',
                         'zh,en' : 'cmn-Hans-CN',
                         'en,zh' : 'en-US'}
        self.pool = pool

    def vop(self, filename, lan='zh', callback=None):
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
            if callback:
                callback(response)
            return response

    def batch_vop_tasks(self, file_list, starts, lan):
        for task_id, file_name in enumerate(file_list):
            yield TaskGoogle(self, file_name, starts[task_id], task_id, lan)

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
