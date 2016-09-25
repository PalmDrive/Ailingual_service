# coding:utf8


class Config(object):
  pass


CONFIG = Config()


def init_config(json_dict):
  CONFIG.__dict__ = json_dict



