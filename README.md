# pipeline_service

# supervisor
```
introduce and configure:
http://www.cnblogs.com/luojianqun/p/5684194.html
install:
pip install supervisor
run servervisor:
supervisord
config file:
/etc/supervisor/conf.d/pipeline_service.conf
restart supervisord:
supervisorctl reload

start pipeline_service:
supervisorctl start pipeline_service
stop pipeline_service:
supervisorctl stop pipeline_service
restart pipeline_service:
supervisorctl restart pipeline_service

status service:
supervisorctl status pipeline_service
service log:
/root/dev/log/pipeline_service.log
```  

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
(staging server: 
export GOOGLE_APPLICATION_CREDENTIALS="/root/dev/pipeline_service/google_credential.json"
)
```

# Makefile
```shell

make install // download all the dependency
make lint // format the imports, use flake8 to check code style
make test // run test
```

# API Documentation
```

Transcribe API: 

    transcribe
    
    Example: http://localhost:8888/transcribe?media_name=name&addr=audio_file_path&lan=zh&company=company_name&upload_oss=true&max_fragment_length=10&requirement=requirement_string&service_providers=providers

@param (required) String: media_name 
 
    The display name of the media to be transcribed  

@param (optional) String: client_id

    The client company id if different from the id of API caller.  
    Default is the same as the API caller's company id.

@param (required) String: addr

    The url to the media

@param (optional) String: lan
    The languages used to transcribe this media
    Options: 
        zh  -  Only use Chinese for transcription. Recommended for pure audio in Chinese. 
        en  -  Only use English for transcription. Recommended for pure audio in English.
        zh,en  -  Use Chinese and English for transcription.  
    Default is zh.

@param (optional) Boolean: upload_oss
    The switch to uploading fragmented media to Aliyun OSS  
    Default is False.
 
@param (optional) Integer: max_fragment_length
    The maximum length in seconds of each fragment sent to transcription service 
    Default is 10.
    
@param (optional) String: requirement
    The requirement for the service to meet on this media.
    Default is '字幕,纯文本,关键词,摘要'.
    
@param (optional) String: service_providers
    The comma(',') separated names of service providers for this transcription task.
    Supported:
        baidu,google
    Default is 'baidu'.
    
@param (optional) Boolean: async
    Default is True.
    
@param (required when async is true) String: callback_url
    The callback url that will be called upon the completion of our transcription process.
    
@param (optional) Boolean: force_fragment_length
    The switch to force fragment length. If it's not enforced, then it won't break up a clip longer than preferred length into smaller pieces. 
    Default is False.

@param (optional) Boolean: create_editor_task
    Whether to create editor task
    Default is False    

@param (required) String: caption_type
    crowdsourcing/editor
    Default is editor.
    
    
外包时transcribe接口需要传的参数：
    addr=
    media_name=
    lan=zh
    client_id=
    requirement=字幕
    async=true
    max_fragment_length=10
    caption_type=editor
    create_editor_task=true
    callback_url=http://www.baidu.com

众包时transcribe接口需要传的参数：
    addr=
    media_name=
    client_id=
    lan=zh
    requirement=字幕
    async=true
    max_fragment_length=16
    caption_type=crowdsourcing
    callback_url=http://www.baidu.com
    upload_oss=true
    force_fragment_length=true

```

```
Summarize API:

    summarize

    curl -X POST -H "app_id: <app_id>" -H "app_key: <app_key>" -H "Content-Type: application/json"
    -d '{
        "title" : "title",
        "content" : "content"
    }' "http://localhost:8888/summarize?async=true&service_providers=tuofeng&callback_url=callbachurl"

Url encoded params
@param (optional) String: service_providers
    The name of service providers for this transcription task.
    Supported:
        boson,tuofeng
    Default is 'boson'.

@param (optional) Boolean: async
    Default is True.

@param (Required when async is true) String: callback_url
    The callback url that will be called upon the completion of our transcription process.

Body params
@param (optional) String: content
    The content to be summarized

@param (optional) String: title
    The title of the content to be summarized

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
    A class to represent a transcription task using Baidu Speech service. /
```

# Access control
```
在leancloud 创建ClientQuota表格， 包含app_id, access_quota, access_count. 这里面app_id 和_user表格里面的app_id 匹配。 access_quota包含该用户授予的访问次数， access_count表示该用户已经访问的次数。 注意其中的次数指的是成功访问的次数。

access_control 方法接受app_id, 返回boolean，True表示能访问， False 表示不能
```
