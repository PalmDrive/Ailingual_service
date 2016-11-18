# coding:utf8
from pydub import AudioSegment
import os

null_file = open(os.devnull, "w")
mp3_file_name = "/Users/lijim001/Downloads/（一）西方思维方式倾向于抽象逻辑思维.mp3"
dst_name = "/Users/lijim001/my_code/palmdrive/pipeline_service/a.mp3"


filename = mp3_file_name
second = 1000
if filename:
    mp3 = AudioSegment.from_mp3(mp3_file_name) # 打开mp3文件

    mp3[:second*10].export(dst_name, format="mp3") # 切割前17.5秒并覆盖保存



