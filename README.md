# pipeline_service

# ffmpeg
```
install ffmpeg:  http://ericholsinger.com/general/install-ffmpeg-on-a-mac/
export PATH=path_to_ffmpeg:$PATH
```

# python
```
virtualenv env
source env/bin/activate
pip install -r requirement.txt

1)python xiaobandeng/server.py
2)curl 'localhost:8888/transcribe?media_name=audio_name&&addr=audio_file_path&&lan=zh'

Google api setup:

export GOOGLE_APPLICATION_CREDENTIALS="path-to-credential-file.json"

```
