#!/usr/bin/env python3

'''An async aria2 JSON-RPC wrapper'''

from __future__ import print_function, absolute_import

import sub

import six
import json
import uuid

from tornado import gen
from tornado.httpclient import AsyncHTTPClient, HTTPError


DEFAULT_RPC_HOST = 'localhost'
DEFAULT_RPC_PORT = '6800'


class Aria2():
    '''Aria2 Wrapper'''

    def __init__(self, host=DEFAULT_RPC_HOST,
            port=DEFAULT_RPC_PORT, secret=None):
        self.host = host
        self.port = port
        self.secret = secret

        self.url = 'http://{}:{}/jsonrpc'.format(host, port)

    def __getRPCBody(self, method, params):
        '''Create RPC body'''
        uid = str(uuid.uuid1())
        params = params if params else []
        if self.secret:
            params.insert(0, 'token:{}'.format(self.secret))

        return json.dumps({
            'jsonrpc': '2.0',
            'id': uid,
            'method': method,
            'params': params,
        })

    @gen.coroutine
    def sendRequest(self, method, params=None):
        '''Send JSON-RPC request to Aria2'''
        body = self.__getRPCBody(method, params)
        http_client = AsyncHTTPClient()

        response = yield http_client.fetch(self.url, method='POST', body=body)
        result = json.loads(response.body.decode('utf-8'))
        raise gen.Return(result['result'])

    @gen.coroutine
    def addUri(self, uris, options=None, position=0):
        '''Add Uri'''
        params = [uris]
        if options:
            params.append(options)
        params.append(position)

        response = yield self.sendRequest('aria2.addUri', params)
        raise gen.Return(response)

    @gen.coroutine
    def remove(self, gid, force=False):
        '''Remove the download denoted by gid '''
        method = 'aria2.forceRemove' if force else 'aria2.remove'
        response = yield self.sendRequest(method, [gid])
        raise gen.Return(response)

    @gen.coroutine
    def pause(self, gid=None, force=False):
        '''Pause download'''
        if not gid:
            method = 'aria2.forcePauseAll' if force else 'aria2.pauseAll'
            params = []
        else:
            method = 'aria2.forcePause' if force else 'aria2.pause'
            params = [gid]
        response = yield self.sendRequest(method, params)
        raise gen.Return(response)

    @gen.coroutine
    def unpause(self, gid=None):
        '''Unpause'''
        if not gid:
            method = 'aria2.unpauseAll'
            params = []
        else:
            method = 'aria2.unpause'
            params = [gid]

        response = yield self.sendRequest(method, params)
        raise gen.Return(response)

    @gen.coroutine
    def tellStatus(self, gid, *keys):
        '''Tell Status'''
        response = yield self.sendRequest('aria2.tellStatus', [gid]+list(keys))
        raise gen.Return(response)

    @gen.coroutine
    def tellActive(self, *keys):
        '''Tell active'''
        response = yield self.sendRequest('aria2.tellActive', list(keys))
        raise gen.Return(response)

    @gen.coroutine
    def tellWaiting(self, offset, num, *keys):
        '''Tell waiting'''
        response = yield self.sendRequest('aria2.tellWaiting', list(keys))
        raise gen.Return(response)

    @gen.coroutine
    def tellStopped(self, offset, num, *keys):
        '''Tell stopped'''
        response = yield self.sendRequest('aria2.tellStopped',
                [offset, num]+list(keys))
        raise gen.Return(response)

    @gen.coroutine
    def getGlobalOption(self):
        '''Get global option'''
        response = yield self.sendRequest('aria2.getGlobalOption')
        raise gen.Return(response)

    @gen.coroutine
    def getGlobalStat(self):
        '''Get global stat'''
        response = yield self.sendRequest('aria2.getGlobalStat')
        raise gen.Return(response)

    @gen.coroutine
    def purgeDownloadResult(self):
        '''Get global stat'''
        response = yield self.sendRequest('aria2.purgeDownloadResult')
        raise gen.Return(response)

    @gen.coroutine
    def removeDownloadResult(self, gid):
        '''Get global stat'''
        response = yield self.sendRequest('aria2.removeDownloadResult', [gid])
        raise gen.Return(response)

    @gen.coroutine
    def isRunning(self):
        if six.PY2:
            import socket
            connectionError = socket.error
        else:
            connectionError = ConnectionRefusedError

        try:
            success, response = yield self.getVersion()
        except connectionError as e:
            raise gen.Return(False)
        else:
            raise gen.Return(True)

    @gen.coroutine
    def getVersion(self):
        response = yield self.sendRequest('aria2.getVersion')
        raise gen.Return(response)

    @gen.coroutine
    def run(self, rpc_port=DEFAULT_RPC_PORT, other_params=''):
        cmd = ('aria2c '
            ' --enable-rpc'
            ' --continue=true'
            ' --rpc-listen-port={}'
            ' --rpc-listen-all=true'
            ' --daemon=true'
            ' {}').format(rpc_port, other_params)

        if self.secret:
            cmd = '{} --rpc-secret {}'.format(cmd, self.secret)

        result, error = yield sub.call_subprocess(cmd)
        raise gen.Return(False if error else True)

    @gen.coroutine
    def stop(self, force=False):
        '''Not work'''
        cmd = 'aria2.forceShutdown' if force else 'aria2.shutdown'
        response = yield self.sendRequest(cmd)

    @gen.coroutine
    def kill(self):
        '''Kill aria2 process'''
        result, error = yield sub.call_subprocess('killall aria2c')
        raise gen.Return(False if error else True)


if __name__ == '__main__':
    import tornado.ioloop

    @gen.coroutine
    def test():

        a = Aria2(secret='helloworld')

        run = yield a.isRunning()
        if run:
            print('Running')
        else:
            run = yield a.run()
            if run:
                print('Run Aria2c successfully')
            else:
                print('Error: {}'.format(error))

        uri = 'http://devstreaming.apple.com/videos/wwdc/2015/704ci202euy/704/704_hd_whats_new_in_cloudkit.mp4?dl=1'

        version = yield a.getVersion()
        print(version)

        res = yield a.addUri([uri], {'dir':'test'})
        print(res)

        status = yield a.tellStatus(res)
        print(status)

        option = yield a.getGlobalOption()
        print(option)

        active = yield a.tellActive()
        print(active)

        purge = yield a.purgeDownloadResult()
        print(purge)

        stopped = yield a.tellStopped(0, 100)
        print(stopped)

        a.kill()

    tornado.ioloop.IOLoop.current().run_sync(test)
