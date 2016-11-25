# coding:utf8
from __future__ import absolute_import

from xiaobandeng.config import load_config
from xiaobandeng.lean_cloud import init
from xiaobandeng.config import CONFIG
import leancloud

env = 'product'
load_config(env)
init(CONFIG)

CLASS_NAME = 'EditorTask'

lean_cloud_class = leancloud.Object.extend(CLASS_NAME)

query = lean_cloud_class.query
query.add_ascending("createdAt")
query.limit(1000)

obj_list = query.find()
print 'total:',len(obj_list)


# obj = obj_list[0]

for obj in obj_list:
    acl = leancloud.ACL()
    acl.set_public_read_access(True)
    acl.set_public_write_access(True)

    obj.set_acl(acl)
    obj.save()
    print obj.id