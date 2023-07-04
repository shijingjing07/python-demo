# 计算密集型,同步/异步差别不大,同步甚至更快
# IO密集型,异步远快于同步
import asyncio
import random
import time

from common import cost


@cost
def sync_t():
    def foo(i):
        time.sleep(0.01)
        return 1

    res = 0
    for i in range(100):
        res += foo(i)
    print("cpu_sync_t res %s" % res)


@cost
def async_t():
    async def foo(i):
        await asyncio.sleep(0.01)
        return 1

    async def run():
        tasks = [foo(i) for i in range(100)]  # coroutine object list
        done, pending = await asyncio.wait(tasks)  # done和pending是set类型,元素为Task(Future子类)
        res = 0
        for i in done:
            res += i.result()
        print("cpu_async_t res %s" % res)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())


@cost
def async_gather_t():
    # gather和wait都会阻塞,直到所有task都完成
    # gather按tasks顺序返回
    # gather直接返回运行结果(asyncio.gather是future类型,为什么能直接打印运行结果?)
    async def foo1():
        await asyncio.sleep(1)
        print("2S")
        await asyncio.sleep(2)
        return 2

    async def foo2():
        print("5S")
        await asyncio.sleep(5)
        return 5

    async def run():
        tasks = [foo2(), foo1()]  # coroutine object list
        f = await asyncio.gather(*tasks)
        for i in f:
            print(i)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())


@cost
def done_t():
    # wait会阻塞,直到所有task都完成
    # wait返回结果是无序的(相对执行顺序)
    async def foo1():
        await asyncio.sleep(1)
        print("2S")
        await asyncio.sleep(2)
        return 2

    async def foo2():
        print("5S")
        await asyncio.sleep(5)
        return 5

    async def run():
        tasks = [foo2(), foo1()]  # coroutine object list
        done, pending = await asyncio.wait(tasks)  # done和pending是set类型,元素为Task(Future子类)
        res = 0
        for i in done:
            print(i.result())
        print("done_t res %s" % res)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())


def await_sync_t():
    async def sleep_t():
        # await 接同步代码测试
        time.sleep(1)
        print("over")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(sleep_t())


def queue_t():
    async def work(i, queue):
        while True:
            v = await queue.get()
            await asyncio.sleep(v)
            queue.task_done()
            print(f"worker {i} sleep {v}")

    async def main():
        queue = asyncio.Queue()
        # 100个消息
        for i in range(100):
            sleep_time = random.uniform(0.1, 1)
            queue.put_nowait(sleep_time)

        # 三个消费者
        tasks = []
        t = asyncio.create_task(work(1, queue))
        tasks.append(t)
        t = asyncio.create_task(work(2, queue))
        tasks.append(t)
        t = asyncio.create_task(work(3, queue))
        tasks.append(t)

        start_time = time.monotonic()
        await queue.join()
        end_time = time.monotonic()
        print(f"cost {end_time-start_time}")

        for t in tasks:
            t.cancel()

    asyncio.run(main())


def subprocess_t():
    async def main():
        asyncio.create_subprocess_shell('python -c "import datetime;print(datetime.datetime.now())"', )
    pass


if __name__ == '__main__':
    # sync_t()  # 155.41
    # async_t()  # 0.15
    # done_t()
    # async_gather_t()
    # await_sync_t()
    queue_t()
