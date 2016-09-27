# coding=utf8
from __future__ import absolute_import

import argparse
import base64
import json
from multiprocessing import Pool

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


    def vop(self, filename, lan='zh'):
        print 'start google vop - ', filename

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
                    'languageCode': 'cmn-Hans-CN',  # a BCP-47 language tag
                },
                'audio': {
                    'content': speech_content.decode('UTF-8')
                }
            })
        response = service_request.execute()
        return response

class TaskGoogle(Task):

    lans = {"zh": ['zh', 'zh', 'zh', 'en', 'en', 'en'],
            "en": ['en', 'en', 'en', 'zh', 'zh', 'zh']
            }

    def __init__(self, tid, file_name, lan='zh', service):
        super(TaskGoogle, self).__init__(tid, file_name)
        self.service = service
        self.max_try = 6
        self._try = 0
        self.lan = lan
        self.url = self.get_url(lan)

    def start(self):
        print 'start google vop on %s' % self.file_name
        self.fetch(self.url)

    def fetch(self, url):
        self.client.fetch(self.get_request(url), self.callback)

    def get_request(self, url):
        http_header = {'Content-Type': 'audio/wav; rate=%d' % self.rate,
                       'Content-Length': str(len(self.body)),
                       }

        return tornado.httpclient.HTTPRequest(url=url, method='POST',
                                              connect_timeout=120,
                                              request_timeout=600,
                                              headers=http_header,
                                              body=self.body
                                              )

    def get_url(self, lan):
        return self.vop_url + '?cuid=' + '123442123233213' + '&token=' + \
               self.token + '&lan=' + lan

    def retry(self):
        self._try += 1
        if self._try < self.max_try:
            self.fetch(self.get_url(self.lans[self.lan][self._try]))
            print 'retry %s...%s' % (self.id, datetime.datetime.now())
        else:
            self.complete()
            self.result = ''

    def callback(self, res):
        if res.error:
            print '%s error:%s' % (self.id, res.error)
            self.retry()
            return

        res = json.loads(res.body)

        if int(res['err_no']) in (3301, 3302):
            # print '%s baidu api error :%s'%(self.id,res['err_no'])
            self.retry()
            return

        if int(res['err_no']) == 0:
            self.result = res["result"][0]
            self.complete()
            # print '%s====>%s'%(self.id,self.result)
            return

        self.result = 'Baidu API error: %d %s' % (res['err_no'], res['err_msg'])
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
