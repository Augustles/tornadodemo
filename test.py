# coding=utf-8

from tornado.testing import gen_test, AsyncTestCase
from tornado.httpclient import AsyncHTTPClient
import tornado
import unittest
import urllib

# 测试tornado是否异步
class MyAsyncTest( AsyncTestCase ):
    # def get_new_ioloop(self):
        # return tornado.ioloop.IOLoop.instance()
    @gen_test(timeout=30)
    def test_xx( self ):
        client = AsyncHTTPClient( self.io_loop )
        path = 'http://localhost:8000?delay=2'
        # path = 'http://localhost:8000/1'
        body = urllib.urlencode({'msg': 'ok'})
        # responses = yield [client.fetch( path, method = 'POST', body=body ) for _ in range( 20 )]
        responses = yield [client.fetch( path, method = 'GET') for _ in range( 20 )]
        for response in responses:
            if response.error:
                raise Exception(response.error)
            print response.body

if __name__ == '__main__':
    unittest.main()
