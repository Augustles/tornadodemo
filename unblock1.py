# coding=utf-8

import tornado.ioloop
from tornado import gen, web
from tornado.httpserver import HTTPServer
from tornado_mysql import pools
import motor
from pymongo import MongoClient
from concurrent.futures import ThreadPoolExecutor
from functools import partial, wraps
import datetime
import time
import tcelery, celery_task
import os

class Executor(ThreadPoolExecutor):
  _instance = None

  def __new__(cls, *args, **kwargs):
    if not getattr(cls, '_instance', None):
      cls._instance = ThreadPoolExecutor(max_workers=10)
    return cls._instance


class FutureResponseHandler(tornado.web.RequestHandler):
  executor = Executor()

  @tornado.web.asynchronous
  @tornado.gen.coroutine
  def get(self, *args, **kwargs):

    # future = Executor().submit(self.ping, 'www.baidu.com')
    # 这里executor线程池异步执行get_news函数
    future = Executor().submit(self.get_news, 10)

    response = yield tornado.gen.with_timeout(
        datetime.timedelta(10),
        future,
        quiet_exceptions=tornado.gen.TimeoutError
    )
    # response是一个future对象, result里存储runner的结果
    # 可以用next_object方法取得

    if response:
        while (yield response.result().fetch_next):
            news = response.result().next_object()
            self.write('title: %(title)s, author: %(author)s' %(news))
        self.finish()
      # print 'response', response.result()

  @tornado.concurrent.run_on_executor
  def get_news(self, n):
    db = self.settings['db']
    ret = db.jianshu.find().limit(n)
    return ret

  @tornado.concurrent.run_on_executor
  def ping(self, url):
    os.system("ping -c 1 {}".format(url))
    return 'after'

db = motor.MotorClient().web
# db = MongoClient().web
app = web.Application(
    [
        (r'/', FutureResponseHandler),
        # (r'/(\d+)', NewsHandler),
    ],
    db=db,
)
if __name__ == '__main__':
    app.listen(8000) # 调用bind方法, 绑定socket端口号
    print('...start server http://127.0.0.1:8000/')
    tornado.ioloop.IOLoop.current().start()
