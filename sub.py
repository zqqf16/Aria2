'''Fork from https://gist.github.com/FZambia/5756470'''

import shlex
import subprocess

from tornado.gen import coroutine, Task, Return
from tornado.process import Subprocess


@coroutine
def call_subprocess(cmd, stdin_data=None, stdin_async=True):
    """call sub process async

        Args:
            cmd: str, commands
            stdin_data: str, data for standard in
            stdin_async: bool, whether use async for stdin
    """
    stdin = Subprocess.STREAM if stdin_async else subprocess.PIPE
    sub_process = Subprocess(shlex.split(cmd),
                             stdin=stdin,
                             stdout=Subprocess.STREAM,
                             stderr=Subprocess.STREAM,)

    if stdin_data:
        if stdin_async:
            yield Task(sub_process.stdin.write, stdin_data)
        else:
            sub_process.stdin.write(stdin_data)

    if stdin_async or stdin_data:
        sub_process.stdin.close()

    result, error = yield [Task(sub_process.stdout.read_until_close),
                           Task(sub_process.stderr.read_until_close)]

    raise Return((result.decode("utf-8"), error.decode("utf-8")))


if __name__ == "__main__":
    from tornado.ioloop import IOLoop

    @coroutine
    def example_main():
        result, error = yield call_subprocess("aria2c --enable-rpc --contisdfnue -D")
        print('result: {}\nerror: {}'.format(result, error))
        IOLoop.instance().stop()

    IOLoop.instance().add_callback(example_main)
    IOLoop.instance().start()
