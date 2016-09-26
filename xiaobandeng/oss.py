import oss2
import os

Access_Key_ID = 'ZblgTWN34znE5dOO'
Access_Key_Secret = 'S09puSorYwkbdyyAjWpqudXQ8mLvl9'

EndpointHost = 'oss-cn-hangzhou.aliyuncs.com'
EndpointHead = 'http://'
BucketName = 'xiaobandeng-staging'
import datetime


# This method should be executed asynchronously
def upload(media_id, file_list):

    auth = oss2.Auth(Access_Key_ID, Access_Key_Secret)
    bucket = oss2.Bucket(auth, EndpointHead + EndpointHost, BucketName)

    key = 'media_fragments/%s/' % media_id

    # upload clips
    for file in file_list:
        filename = os.path.basename(file)
        # print "%s ----start@----%s"%(filename,datetime.datetime.now())
        bucket.put_object_from_file(key + filename, file)
        # print "%s ----end@----%s"%(filename,datetime.datetime.now())

def media_fragment_url(media_id, file_name):
    return "%s%s.%s/media_fragments/%s/%s" % (EndpointHead, BucketName, EndpointHost, media_id, os.path.basename(file_name))