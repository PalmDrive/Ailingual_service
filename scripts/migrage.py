from __future__ import absolute_import

from xiaobandeng.config import load_config
from xiaobandeng.lean_cloud import init
from xiaobandeng.config import CONFIG
from xiaobandeng.lean_cloud import lean_cloud

env = 'develop'
load_config(env)
init(CONFIG)

media_id_list = ['01cebbd9-ce85-4798-933b-432bc51d7844',
                 'c31b13ad-069f-4826-8e16-44bf7d78a1d3',
                 '6c05e738-cb89-45ba-b47f-5ef64ab97ba7',
                 'f7419a52-6173-425b-99ab-758424a0e10b',
                 'af8f3ad5-eb1a-4867-955e-100c92a30bbe',
                 'be749fe2-ec75-4855-a088-44755830948c',
                 '345ba370-3f48-44e2-b1e3-d6ba4fb8bd2e']

lc = lean_cloud.LeanCloud()
media_id = media_id_list[0]
media = lc.get_media(media_id)

print dir(media)

