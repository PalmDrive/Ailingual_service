import tornado.web
import tornado.httpserver
import tornado.ioloop
import json, urllib2

class TestHandler(tornado.web.RequestHandler):
    def post(self, *args, **kwargs):
        print '--'*20
        print 'post data :',urllib2.unquote(self.request.body)
        print '--'*20
        self.write("succ")
        self.finish()


tornado.httpserver.HTTPServer(
    tornado.web.Application([("/test", TestHandler)])
).listen(10000)

tornado.ioloop.IOLoop.instance().start()


#test
#GET http://localhost:8888/transcribe?media_name=audio_leancloud_class_name&addr=http%3A%2F%2Fxiaobandeng-staging.oss-cn-hangzhou.aliyuncs.com%2Fpipeline_videos%2Fserial-s02-e09.mp3&lan=en&company=company_nameee&upload_oss=true&max_fragment_length=10&async=1&callback=http%3A%2F%2Flocalhost%3A10000%2Ftest
#app_key: 34363bc78d6c
#app_id: e3f9e83a-91df-11e6-852f