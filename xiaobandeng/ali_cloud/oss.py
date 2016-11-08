from __future__ import absolute_import

import os

import oss2

from xiaobandeng.config import CONFIG

def media_fragment_url(media_id, file_name):
    return "%s%s.%s/media_fragments/%s/%s" % (CONFIG.OSS_ENDPOINT_HEAD,
                                              CONFIG.OSS_BUCKET_NAME,
                                              CONFIG.OSS_ENDPOINT_HOST,
                                              media_id,
                                              os.path.basename(file_name))



# This method should be executed asynchronously
def upload(media_id, task_group, cloud_db):
    auth = oss2.Auth(CONFIG.OSS_ACCESS_KEY_ID, CONFIG.OSS_ACCESS_KEY_SECRET)
    bucket = oss2.Bucket(auth,
                         CONFIG.OSS_ENDPOINT_HEAD + CONFIG.OSS_ENDPOINT_HOST,
                         CONFIG.OSS_BUCKET_NAME)

    key = 'media_fragments/%s/' % media_id

    # upload clips
    # marking task.on_oss for batch call leancloud upload api
    # fragments fragment_order is task.id
    for task in task_group.tasks:
        task.on_oss = False
        f = task.file_name
        for i in xrange(3):
            # print "%s ----start@----"%(filename)
            filename = os.path.basename(f)
            try:
                result = bucket.put_object_from_file(key + filename, f)
            except oss2.exceptions.OssError as err:
                print err
                continue
            # print "%s ----end@----%s %s" % (filename, str(result.status), str(result.resp))
            if str(result.status) == "200":
                task.on_oss = True
                cloud_db.set_fragment_src(cloud_db.fragments[task_group.tasks.index(task)],
                                          media_fragment_url(media_id, f))
                break
            else:
                print "%s ----uploading process failed----%s" % (
                    filename, str(result.status))


