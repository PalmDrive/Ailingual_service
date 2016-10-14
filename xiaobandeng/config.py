# coding:utf8
from __future__ import absolute_import

import json
import logging
import os
import sys


class Config(object):
    pass


CONFIG = Config()


def init_config(json_dict):
    CONFIG.__dict__ = json_dict


def load_config(env):
    pwd = os.path.dirname(__file__)
    sys.path.append(pwd)
    config_file = os.path.join(pwd, "config", env + ".json")
    config_dict = json.load(open(config_file))
    init_config(config_dict)

    logging.info("------current environment is \"%s\","
                 "using config file: \"%s\"" % (env, config_file))
