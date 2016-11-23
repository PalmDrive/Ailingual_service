from  load_env import *

load_env("production")


import leancloud

CLASS_NAME = 'EditorTask'

lean_cloud_class = leancloud.Object.extend(CLASS_NAME)
query =  lean_cloud_class.query


query.equal_to("task_type",1)


result_list = query.find()
for i in result_list:
    print i.id
    i.destroy()
