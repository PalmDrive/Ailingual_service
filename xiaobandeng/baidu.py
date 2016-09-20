# coding=utf-8
from __future__ import absolute_import

import contextlib
import httplib2
import json
import os
import wave
import sys
from uuid import getnode as get_mac


Api_Key = "Ki1wq6cYASyrFFgMNQtGAmz5"
Secret_Key = "1226a59f3407d28d924012d76ee2f691"


class BaiduNLP(object):
    auth_url = "https://openapi.baidu.com/oauth/2.0/token?"\
            "grant_type=client_credentials&client_id=%s&client_secret=%s"
    vop_url = "http://vop.baidu.com/server_api"
    inited = False

    def init_access_token(self):
        h = httplib2.Http(".cache")
        url = self.auth_url % (Api_Key, Secret_Key)
        try:
            resp, content = h.request(url)
            if resp.status != 200:
                raise Exception(
                        'failed to get access token %s %s' % (resp, content))
            data = json.loads(content)
            self.access_token = data['access_token']
            self.session_secret = data['session_secret']
            self.session_key = data['session_key']
            self.refresh_token = data['refresh_token']
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
            frames = w.getnframes()
            rate = w.getframerate()
            duration = frames / float(rate)
            h = httplib2.Http()
            body = w.readframes(w.getnframes())
            http_header = {
                'Content-Type': 'audio/wav; rate=%d' % rate,
                'Content-Length': str(len(body)),
            }

            result = ''
            lans = []
            if lan == 'zh':
                lans = ['zh', 'zh', 'zh', 'en', 'en', 'en']
            else:
                lans = ['en', 'en', 'en', 'zh', 'zh', 'zh']
            for retryCount in range(0, 6):
                resp, content = h.request(
                    uri=self.vop_url + '?cuid=' + str(
                        get_mac()) + '&token=' + str(self.access_token) + '&lan=' + lans[retryCount],
                    method='POST',
                    headers=http_header,
                    body=body,
                )
                if resp.status == 200:
                    data = json.loads(content)
                    if int(data['err_no']) == 0:
                        result = data['result'][0]
                        break
                    elif int(data['err_no']) != 3301 and int(data['err_no']) != 3302:
                        result = 'Baidu API error: %d %s' % (int(data['err_no']), data['err_msg'])
                        break
                    else:
                        print('Baidu API error: %d %s ... retry ...' % (int(data['err_no']), data['err_msg']))
                else:
                    result = u'这句话翻译失败: ' + str(content)

            return duration, result


if __name__ == "__main__":
    b = BaiduNLP()
    b.init_access_token()
    args = sys.argv[1:]
    path = "/Users/yonglin/playground/pipeline_service/test_file/pchunk-2.wav"
    if len(args) > 0:
        path = args[0]
    lan = 'zh'
    if len(args) > 1:
        lan = args[1]
    duration, result = b.vop(path, lan)
    print(duration)
    print(result)
