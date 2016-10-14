# -*- coding: utf-8 -*-

from __future__ import absolute_import


from .base import BaseHandler

class TestHandler(BaseHandler):
    def get(self):
        self.write("test ok")

