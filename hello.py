#!/usr/bin/env python
# coding=utf-8

import tornado.ioloop
import tornado.web

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write('hello world') # get方法

# 绑定路由
application = tornado.web.Application([(r'/', MainHandler),])

if __name__ == '__main__':
    application.listen(8888) # 绑定端口
    tornado.ioloop.IOLoop.current().start()
