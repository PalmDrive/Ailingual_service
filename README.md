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
2)curl 'localhost:8888/transcribe?media_name=name&addr=audio_file_path&lan=zh&company=company_name&upload_oss=true&max_fragment_length=10'

Google api setup:

export GOOGLE_APPLICATION_CREDENTIALS="path/to/google_credential.json"
```

# API Documentation
```

Transcribe API: 

    transcribe
    
    Example: http://localhost:8888/transcribe?media_name=name&addr=audio_file_path&lan=zh&company=company_name&upload_oss=true&max_fragment_length=10&requirement=requirement_string

@param (required) String: media_name 
 
    The display name of the media to be transcribed  

@param (required) String: addr

    The url to the media

@param (optional) String: lan
    The language used to transcribe this media
    Options: 
        zh  -  Only use Chinese for transcription. Recommended for pure audio in Chinese. 
        en  -  Only use English for transcription. Recommended for pure audio in English.
        zh,en  -  Use Chinese for transcription first. If not recognized, then use English. Recommended for audio in most Chinese and little English.  
        en,zh  -  Use English for transcription first. If not recognized, then use Chinese. Recommended for audio in most English and little Chinese.
    Default is zh.

@param (optional) Boolean: upload_oss
    The switch to uploading fragmented media to Aliyun OSS  
    Default is False.
 
@param (optional) Integer: max_fragment_length
    The maximum length in seconds of each fragment sent to transcription service 
    Default is 10.
    
@param (optional) String: requirement
    The requirement for the service to meet on this media.
    Default is '字幕/纯文本/关键词/摘要'.

```

# Architecture Design
```

@class TaskGroup:
    TaskGroup object is used to group tasks and excute a callback when all the tasks in the group are completed.

@class Task:
    A general class to represent a task: transcription, key words extraction, summarization, censoring. It's usually subclassed to do more specific work(See TranscriptionTask).

@class TranscriptionTask:
    A class to represent a task used to transcribe.
    
@class BaiduTask:
    A class to represent a transcription task using Baidu Speech service. 
```
