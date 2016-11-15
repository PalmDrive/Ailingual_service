from __future__ import absolute_import

from xiaobandeng.config import load_config
from xiaobandeng.lean_cloud import init
from xiaobandeng.config import CONFIG
from xiaobandeng.lean_cloud import lean_cloud
import leancloud

env = 'product'
load_config(env)
init(CONFIG)

CLASS_NAME = 'EditorTask'

lean_cloud_class = leancloud.Object.extend(CLASS_NAME)

lean_cloud_class
