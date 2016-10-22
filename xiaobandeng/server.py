# -*- coding: utf-8 -*-

from __future__ import absolute_import

import logging
import os
import sys

import tornado.httpclient
import tornado.httpserver
import tornado.ioloop
import tornado.web

from xiaobandeng.config import CONFIG
from xiaobandeng.config import load_config
from xiaobandeng.handlers.medium.lrc import LrcHandler
from xiaobandeng.handlers.medium.srt import SrtHandler
from xiaobandeng.handlers.transcribe import TranscribeHandler
from xiaobandeng.handlers.medium.caption import CaptionHandler
from xiaobandeng.handlers.medium.task import EditorTaskHandler
from xiaobandeng.lean_cloud import init


def make_app(use_autoreload):
    return tornado.web.Application([
                                       (r"/transcribe", TranscribeHandler),
                                       (r"/medium/(.*)/srt", SrtHandler),
                                       (r"/medium/(.*)/lrc", LrcHandler),
                                       (r"/medium/(.*)/caption", CaptionHandler),
                                       (r"/medium/(.*)/create_task",EditorTaskHandler),
                                   ], autoreload=use_autoreload)


def main():
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

    reload(sys)
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    sys.setdefaultencoding("utf-8")

    define("port", default=8888, help="run on this port", type=int)
    define("env", default="develop", help="develop production staging")
    define("use_autoreload", default=False, help="set debug to use auto reload")
    define("unix_socket", default=None, help="unix socket path")
    tornado.options.parse_command_line()

    env = os.environ.get("PIPELINE_SERVICE_ENV")

    if not env:
        env = options.env
    load_config(env)
    init(CONFIG)

    server = tornado.httpserver.HTTPServer(make_app(options.use_autoreload),
                                           xheaders=True)
    if options.unix_socket:
        server.add_socket(bind_unix_socket(options.unix_socket))
    else:
        server.listen(options.port)
    logging.info("running on %s" % (options.unix_socket or options.port))

    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
