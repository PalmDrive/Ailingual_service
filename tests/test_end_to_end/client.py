# Install the Python Requests library:
# `pip install requests`

import requests


def send_request():
    try:
        response = requests.get(
            url="http://localhost:8888/transcribe",
            params={
                "media_name": "audio_leancloud_class_name",
                "addr": "http://xiaobandeng-staging.oss-cn-hangzhou.aliyuncs.com/pipeline_videos/serial-s02-e09.mp3",
                "lan": "en",
                "company": "company_nameee",
                "upload_oss": "true",
                "max_fragment_length": "10",
                "async": "true",
                "callback": "http://localhost:10000/test",
            },
            headers={
                "app_key": "34363bc78d6c",
                "app_id": "e3f9e83a-91df-11e6-852f",
            },
        )
        print('Response HTTP Status Code: {status_code}'.format(
            status_code=response.status_code))
        print('Response HTTP Response Body: {content}'.format(
            content=response.content))
    except requests.exceptions.RequestException:
        print('HTTP Request failed')


if __name__ == '__main__':
    send_request()