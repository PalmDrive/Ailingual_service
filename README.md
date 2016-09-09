# pipeline_service

# ffmpeg
install ffmpeg:  http://ericholsinger.com/general/install-ffmpeg-on-a-mac/
export PATH=path_to_ffmpeg:$PATH

# python
virtualenv env
source env/bin/activate
pip install -r requirement.txt

1)python xiaobendeng/server.py
2)curl 'localhost:8888/translate?object=audio_leancloud_class_name&&addr=audio_file_path' 
