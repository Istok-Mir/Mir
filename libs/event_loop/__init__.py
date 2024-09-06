import asyncio
from threading import Thread
from typing import Optional, Awaitable

__loop: Optional[asyncio.AbstractEventLoop] = None
__thread: Optional[Thread] = None

def run_future(future: Awaitable):
    global __loop
    if __loop:
        f = asyncio.ensure_future(future, loop=__loop)
        __loop.call_soon_threadsafe(asyncio.ensure_future, f)


def setup_event_loop():
    print('loop: starting')
    global __loop
    global __thread
    if __loop:
        print('loop: already created')
        return
    __loop = asyncio.new_event_loop()
    __thread = Thread(target=__loop.run_forever)
    __thread.start()
    print("loop: started")


def shutdown_event_loop():
    print("loop: stopping")
    global __loop
    global __thread

    if not __loop:
        print('no loop to shutdown.')

    def __shutdown():
        for task in asyncio.all_tasks():
            task.cancel()
        asyncio.get_event_loop().stop()

    if __loop and __thread:
        __loop.call_soon_threadsafe(__shutdown)
        __thread.join()
        __loop.run_until_complete(__loop.shutdown_asyncgens())
        __loop.close()
    __loop = None
    __thread = None
    print("loop: stopped")

