# -*- coding: utf-8 -*-

import os
import json
import logging
import tornado.httpclient
import tornado.ioloop
import tornado.web
import tornado.httpserver
import env_config

from handlers.test import TestHandler
from handlers.transcribe import  TranscribeHandler
from handlers.medium.lrc import LrcHandler
from handlers.medium.srt import SrtHandler


def make_app(use_autoreload):
    return tornado.web.Application([
                                       (r"/test", TestHandler),
                                       (r"/transcribe", TranscribeHandler),
                                       (r"/medium/(.*)/srt", SrtHandler),
                                       (r"/medium/(.*)/lrc", LrcHandler),
                                   ], autoreload=use_autoreload)


if __name__ == "__main__":
    """
    set system environ "PIPELINE_SERVICE_ENV"  to use different environment,
    choices are "develop product staging".
    or use command line option  %process_name  --env == [envname].
    """

    from tornado.options import define, options
    from tornado.netutil import bind_unix_socket

    # when python writes unicode to stdout,it will encode unicode string
    # using  sys.getdefaultencoding()
    # on a linux ,it defaults to ascii,so got an error like this
    # "UnicodeEncodeError: "ascii" codec can"t encode character  u"\uxxxx"
    # in position 183: ordinal not in range(128)"
    # use sys.getdefaultencoding() to get current val

    import sys

    reload(sys)
    sys.setdefaultencoding("utf-8")

    define("port", default=8888, help="run on this port", type=int)
    define("env", default="develop", help="develop production staging")
    define("use_autoreload", default=True, help="set debug to use auto reload")
    define("unix_socket", default=None, help="unix socket path")
    tornado.options.parse_command_line()

    env = os.environ.get("PIPELINE_SERVICE_ENV")
    if not env:
        env = options.env

    pwd = os.path.dirname(__file__)
    sys.path.append(pwd)
    config_file = os.path.join(pwd, "config", env + ".json")
    config_dict = json.load(open(config_file))
    env_config.init_config(config_dict)

    logging.info("------current environment is \"%s\","
                 "using config file: \"%s\"" % (env, config_file))

    # logging.info(env_config.CONFIG.__dict__)

    server = tornado.httpserver.HTTPServer(make_app(options.use_autoreload),
                                           xheaders=True)
    if options.unix_socket:
        server.add_socket(bind_unix_socket(options.unix_socket))
    else:
        server.listen(options.port)
    logging.info("running on %s" % (options.unix_socket or options.port))

    tornado.ioloop.IOLoop.instance().start()
