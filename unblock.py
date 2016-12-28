# coding=utf-8

from concurrent.futures import ThreadPoolExecutor
from functools import partial, wraps
import time
import tornado.ioloop
import tornado.web
from tornado.options import define, options

define("port", default=8000, help="run on the given port", type=int)
EXECUTOR = ThreadPoolExecutor(max_workers=4)
def unblock(f):
    @tornado.web.asynchronous
    @wraps(f)
    def wrapper(*args, **kwargs):
        self = args[0]
        def callback(future):
            self.write(future.result())
            self.finish()
        EXECUTOR.submit(
            partial(f, *args, **kwargs)
        ).add_done_callback(
            lambda future: tornado.ioloop.IOLoop.instance().add_callback(
                partial(callback, future)))
    return wrapper


class JustNowHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("i hope just now see you")

class SleepHandler(tornado.web.RequestHandler):
    @unblock
    def get(self, n):
        time.sleep(float(n))
        return "Awake! %s" % time.time()

class SleepAsyncHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self, n):
        def callback(future):
            self.write(future.result())
            self.finish()
        EXECUTOR.submit(
            partial(self.get_, n)
        ).add_done_callback(
            lambda future: tornado.ioloop.IOLoop.instance().add_callback(
                partial(callback, future)))
    def get_(self, n):
        time.sleep(float(n))
        return "Awake! %s" % time.time()
application = tornado.web.Application([
    (r"/justnow", JustNowHandler),
    (r"/sleep/(\d+)", SleepHandler),
    (r"/sleep_async/(\d+)", SleepAsyncHandler),
])

if __name__ == "__main__":
   application.listen(options.port)
   tornado.ioloop.IOLoop.instance().start()
