import oss2
import os
from env_config import CONFIG


# This method should be executed asynchronously
def upload(media_id, file_list):
    auth = oss2.Auth(CONFIG.OSS_ACCESS_KEY_ID, CONFIG.OSS_ACCESS_KEY_SECRET)
    bucket = oss2.Bucket(auth, CONFIG.OSS_ENDPOINT_HEAD + CONFIG.OSS_ENDPOINT_HOST,
                         CONFIG.OSS_BUCKET_NAME)

    key = 'media_fragments/%s/' % media_id

    # upload clips
    for f in file_list:
        filename = os.path.basename(f)
        # print "%s ----start@----%s"%(filename,datetime.datetime.now())
        bucket.put_object_from_file(key + filename, f)
        # print "%s ----end@----%s"%(filename,datetime.datetime.now())


def media_fragment_url(media_id, file_name):
    return "%s%s.%s/media_fragments/%s/%s" % (CONFIG.OSS_ENDPOINT_HEAD,
                                              CONFIG.OSS_BUCKET_NAME,
                                              CONFIG.OSS_ENDPOINT_HOST,
                                              media_id,
                                              os.path.basename(file_name))
