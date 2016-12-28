#!/usr/bin/env python
# coding=utf-8

# tornado主要分为三大核心模块, IOLoop, IOStream, HTTPConnection
# 1. IOLoop是调度的核心模块, tornado把所有的socket描述符都注册到IOLoop
# 注册时候指明回调函数, IOLoop不断监听IO事件, 一旦发现某个socket可读写
# 就注册其回调函数
# tornado为了实现高并发和高性能使用了IOLoop来处理socket读写事件
# IOLoop基于epoll,可以高效响应网络事件
# 2. IOStream实现了socket异步读写, tornado实现IOStream类来处理异步读写
# 3. HTTPConnection是用来处理http请求的

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

EXECUTOR = ThreadPoolExecutor(max_workers=10)
def unblock(f):
    @tornado.web.asynchronous
    @wraps(f)
    def wrapper(*args, **kwargs):
        self = args[0]
        def callback(future):
            # 这里返回的future对象
            self.write(future.result())
            self.finish()
        EXECUTOR.submit(
            partial(f, *args, **kwargs)
        ).add_done_callback(
            lambda future: tornado.ioloop.IOLoop.instance().add_callback(
                partial(callback, future)))
    return wrapper

class Executor(ThreadPoolExecutor):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not getattr(cls, '_instance', None):
            cls._instance = ThreadPoolExecutor(max_workers=10)
        return cls._instance

class NewsHandler(web.RequestHandler):
    # coroutine可以将一个普通函数变为异步函数,他会返回一个future对象
    # @web.asynchronous
    # 实现异步的方式有两种,一种是yield挂起函数,另一种是使用类线程池的方式
    # 异步实现1
    @unblock
    def get3(self):
        time.sleep(float(1.2))
        return {'status unblock': 1, 'msg': 'success'}
    # 异步实现2
    @gen.coroutine
    def get1(self):
        yield gen.sleep(float(1.2))
        self.write({'status gen': 1, 'msg': 'success'})
    # 异步实践 连接mongodb 1(yield)
    # 还有可以使用类似线程池(fail)
    # @unblock
    # 当使用asynchronous时需要手动self.finish()
    # @web.asynchronous

    @gen.coroutine
    def get(self):
        # 这一行执行还是会阻塞需要时间, 可以使用任务队列
        # 报错 is not JSON serializable
        # ret = yield gen.Task(celery_task.sleep.apply_async, args=[3])
        # ret = celery_task.sleep.apply_async(args=[1.2])
        # 这一行执行还是会阻塞需要时间,  这里用yield挂起
        # 还可以使用任务队列
        cursor = yield gen.Task(self.get_news, 10)
        # cursor = yield gen.Task(celery_task.sleep.apply_async, args=[3])
        while (yield cursor.fetch_next):
            news = cursor.next_object()
            self.write('title: %(title)s, author: %(author)s' %(news))
        self.finish()

    @gen.coroutine
    def get_news(self, n):
        db = self.settings['db']
        ret = db.jianshu.find().limit(n)
        return ret
        # cursor = db.jianshu.find()
        # # motor封装的cursor, 他是一个类似生成器的
        # print cursor
        # while (yield cursor.fetch_next):
            # news = cursor.next_object()
            # self.write('title: %(title)s, author: %(author)s' %(news))
        # self.finish()

        # db.messages.find().sort([('_id', -1)]).each(self._get_news)
        # self.write('hello world') # get方法输出
        # # self.redirect('/test') # 进行页面跳转
        # self.finish() # 页面跳转或者渲染模板不需要结束

    def _get_news(self, messages, error):
        if messages:
            self.write('<li>%s</li>' %messages['msg'])
        else:
            self.finish()

    @web.asynchronous
    def post(self):
        msg = self.get_argument('msg')
        print msg
        self.settings['db'].messages.insert(
            {'msg': msg},
            callback=self._on_response
        )

    def _on_response(self, result, error):
        print result
        if result:
            self.write({'insert done': 'ok'})
            self.finish()
        else:
            self.write({'insert': 'error'})
            self.finish()
            # self.redirect('/')

# 绑定路由
db = motor.MotorClient().web
# db = MongoClient().web
app = web.Application(
    [
        (r'/', NewsHandler),
        # (r'/(\d+)', NewsHandler),
    ],
    db=db,
)

if __name__ == '__main__':
    app.listen(8000) # 调用bind方法, 绑定socket端口号
    # 将初始化的listen socket注册到ioloop池中,
    # 这时已经开始监听客户端的请求
    # 开始ioloop, 这个为单进程服务器
    print('...start server http://127.0.0.1:8000/')
    tornado.ioloop.IOLoop.current().start()
    # 以下为多进程服务器(4个进程)
    # server = HTTPServer(app)
    # server.bind(8100)
    # server.start(4)
    # tornado.ioloop.IOLoop.current().start()
