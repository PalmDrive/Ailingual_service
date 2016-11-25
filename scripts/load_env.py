# coding:utf8

from __future__ import absolute_import

from xiaobandeng.config import load_config
from xiaobandeng.lean_cloud import init
from xiaobandeng.config import CONFIG


def load_env(env="staging"):
    load_config(env)
    init(CONFIG)
