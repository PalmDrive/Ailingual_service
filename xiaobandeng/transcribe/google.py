# coding=utf8
from __future__ import absolute_import

import argparse
import base64

import requests
from concurrent.futures import ThreadPoolExecutor

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
from .task import TranscriptionTask
from tornado import concurrent, ioloop

class CustomHttp(object):
  def __init__(self, timeout=None):
    self.timeout = timeout

  def request(self, uri, method='GET', body=None, headers=None,
              redirections=None, connection_type=None):
    if connection_type is not None:
      uri = '%s://%s' % (connection_type, uri)
    resp = requests.request(method=method, url=uri, data=body, headers=headers,
                            timeout=self.timeout)
    resp.status = resp.status_code
    return resp, resp.content

DISCOVERY_URL = ('https://{api}.googleapis.com/$discovery/rest?'
                 'version={apiVersion}')

class TaskGoogle(TranscriptionTask):

    def __init__(self, service, executor, file_name, start_time, order=None, lan='cmn-Hans-CN', completion_callback=None):
        super(TaskGoogle, self).__init__(file_name, start_time, order, lan, completion_callback)
        self.service = service
        self.executor = executor
        self.lan = lan
        self.file_name = file_name

    def source_name(self):
        return 'google'

    def start(self):
        with open(self.file_name, 'rb') as speech:
            # Base64 encode the binary audio file for inclusion in the JSON
            # request.
            speech_content = base64.b64encode(speech.read())
        f = self.get_request(speech_content, self.lan)
        f.add_done_callback(self.callback)
        return f

    @concurrent.run_on_executor
    def get_request(self, speech_content, lan='cmn-Hans-CN'):
        lanCode = lan

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
        return service_request.execute()

    def callback(self, f):
        if f.exception():
            self.result = 'Google API error: %s' % f.exception()

        res = f.result()
        print "google speech API result - ", res
        results = []
        if 'results' in res:
            result_arr = res['results']
            for dict in result_arr:
                al = dict['alternatives'][0]
                results.append(al['transcript'])
        self.result = results
        self.complete()

class GoogleASR(object):
    # Application default credentials provided by env variable
    # GOOGLE_APPLICATION_CREDENTIALS
    def __init__(self, pool = None):
        self.auth_url = 'https://www.googleapis.com/auth/cloud-platform'
        credentials = GoogleCredentials.get_application_default().create_scoped(
            [self.auth_url])
        http = CustomHttp()
        credentials.authorize(http)
        self.service = discovery.build(
            'speech', 'v1beta1', http=http, discoveryServiceUrl=DISCOVERY_URL)

        self.executor = ThreadPoolExecutor(max_workers=4)
        self.lanCodes = {'zh' : 'cmn-Hans-CN',
                         'en' : 'en-US'}


    def vop(self, file_name, lan):
        TaskGoogle(self.service, self.executor, file_name, 0, 0, lan).start()

    def batch_vop_tasks(self, file_list, starts, lan):
        for task_id, file_name in enumerate(file_list):
            for l in lan.split(','):
                yield TaskGoogle(self.service, self.executor, file_name, starts[task_id], task_id, self.lanCodes[l])

def main(speech_file):
    """Transcribe the given audio file.

    Args:
        speech_file: the name of the audio file.
    """
    g = GoogleASR()
    response = g.vop(speech_file, lan='cmn-Hans-CN')
    print response

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'speech_file', help='Full path of audio file to be recognized')
    args = parser.parse_args()
    main(args.speech_file)
