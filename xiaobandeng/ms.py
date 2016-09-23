# coding=utf-8
from __future__ import absolute_import

import base64
import contextlib
import httplib2
import json
import os
import uuid
import wave
import sys
from uuid import getnode as get_mac


Subscription_Key1 = "05ef0296aafc4f93944a38f508fab228"
Subscription_Key2 = "41584946ac084973bad768ff838552cd"


class MsNLP(object):
    auth_url = "https://oxford-speech.cloudapp.net/token/issueToken?" \
        "grant_type=client_credentials&client_id=%s&client_secret=%s" \
        "&scope=https://speech.platform.bing.com"

    vop_url = "https://speech.platform.bing.com/recognize?"
    inited = False

    def init_access_token(self):
        h = httplib2.Http(".cache")
        url = self.auth_url % (Subscription_Key1, Subscription_Key1)
        print url
        try:
            resp, content = h.request(
                url,
                method='POST',
                headers={"Content-Type": "application/x-www-form-urlencoded"})
            if resp.status != 200:
                raise Exception(
                        'failed to get access token %s %s' % (resp, content))
            data = json.loads(content)
            self.access_token = data['access_token']
            self.expires_in = data['expires_in']
            self.inited = True
        except httplib2.ServerNotFoundError as e:
            raise Exception('failed to get access token %s' % str(e))

    @staticmethod
    def getSize(filename):
        st = os.stat(filename)
        return st.st_size

    def vop(self, filename, lan='zh'):
        print 'start vop', filename
        if not self.inited:
            raise Exception('module has not been initialized')

        with contextlib.closing(wave.open(filename, 'r')) as w:
            url = (self.vop_url + "Version=3.0" + "&"
                   + "requestid=" + str(uuid.uuid4()) + "&"
                   + "appID = D4D52672-91D7-4C74-8AD8-42B1D98141A5" + "&"
                   + "format=json" + "&"
                   + "local=zh-cn" + "&"
                   + "scenarios=ulm" + "&"
                   + "instanceid=" + get_mac())
            h = httplib2.Http()
            body = w.readframes(w.getnframes())
            http_header = {
                'Content-Type': 'audio/wav; samplerate=16000',
                'Authorization': 'Bearer ' + base64.encodestring(
                    self.access_token)
            }

            for retryCount in range(0, 6):
                resp, content = h.request(
                    uri=url,
                    method='POST',
                    headers=http_header,
                    body=body,
                )
                if resp.status == 200:
                    data = json.loads(content)
                    print data


if __name__ == "__main__":
    b = MsNLP()
    b.init_access_token()
    args = sys.argv[1:]
    path = "/Users/yonglin/playground/pipeline_service/test_file/pchunk-2.wav"
    if len(args) > 0:
        path = args[0]
    lan = 'zh'
    if len(args) > 1:
        lan = args[1]
    b.vop(path, lan)
