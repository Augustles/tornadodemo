# coding=utf-8

from tornado import gen
import tornado

@gen.coroutine
def worker():
    print 'worker start...'

@gen.coroutine
def master():
    print 'master start...'

tornado.ioloop.IOLoop.instance().start()
