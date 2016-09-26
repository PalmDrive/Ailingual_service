import oss2
import os
from env_config import  CONFIG

# OSS_Access_Key_ID = 'ZblgTWN34znE5dOO'
# OSS_Access_Key_Secret = 'S09puSorYwkbdyyAjWpqudXQ8mLvl9'
#
# OSS_EndpointHost = 'oss-cn-hangzhou.aliyuncs.com'
# OSS_EndpointHead = 'http://'
# OSS_BucketName = 'xiaobandeng-staging'


# This method should be executed asynchronously
def upload(media_id, file_list):

    auth = oss2.Auth(CONFIG.OSS_Access_Key_ID, CONFIG.OSS_Access_Key_Secret)
    bucket = oss2.Bucket(auth, CONFIG.OSS_EndpointHead + CONFIG.OSS_EndpointHost,
                         CONFIG.OSS_BucketName)

    key = 'media_fragments/%s/' % media_id

    # upload clips
    for file in file_list:
        filename = os.path.basename(file)
        # print "%s ----start@----%s"%(filename,datetime.datetime.now())
        bucket.put_object_from_file(key + filename, file)
        # print "%s ----end@----%s"%(filename,datetime.datetime.now())

def media_fragment_url(media_id, file_name):
    return "%s%s.%s/media_fragments/%s/%s" % (CONFIG.OSS_EndpointHead,
                                              CONFIG.OSS_BucketName,
                                              CONFIG.OSS_EndpointHost,
                                              media_id,
                                              os.path.basename(file_name))