# coding=utf8
from __future__ import absolute_import

import argparse
import base64
import json

from googleapiclient import discovery
import httplib2
from oauth2client.client import GoogleCredentials


DISCOVERY_URL = ('https://{api}.googleapis.com/$discovery/rest?'
                 'version={apiVersion}')


class GoogleASR(object):
# Application default credentials provided by env variable
# GOOGLE_APPLICATION_CREDENTIALS
    def init_speech_service(self):
        credentials = GoogleCredentials.get_application_default().create_scoped(
            ['https://www.googleapis.com/auth/cloud-platform'])
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

def main(speech_file):
    """Transcribe the given audio file.

    Args:
        speech_file: the name of the audio file.
    """
    g = GoogleASR()
    g.init_speech_service()
    response = g.vop(speech_file, lan='zh')
    print(json.dumps(response))
    print(response['results'][0]['alternatives'][0]['transcript'])

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'speech_file', help='Full path of audio file to be recognized')
    args = parser.parse_args()
    main(args.speech_file)
