from typing import Callable, Any, Annotated, Generator

import redis.asyncio as redis
import redis as redis_sync
from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.db import engine
from app.utils import RateLimiter


async def get_redis_connection():
    r = await redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        encoding="utf-8",
    )
    return r


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


DBSession = Annotated[Session, Depends(get_db)]


class RedisTaskQueue:
    def __init__(
        self,
        redis_host: str,
        redis_port: int,
        concur_key: str,
        wait_key: str,
        concur_size: int,
    ):
        self.redis = redis.Redis(host=redis_host, port=redis_port)
        self.concur_key = concur_key
        self.wait_key = wait_key
        self.concur_size = concur_size

    def put(
        self, _trigger_id: str, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> None:
        # 检查等待队列的大小
        if self.redis.llen(self.wait_key) >= self.concur_size:
            raise Exception("Task queue is full")

        # 将任务信息添加到等待队列
        task_info = (
            f"{_trigger_id}:{func.__name__}"  # 这里简化处理，只存储触发器ID和函数名
        )
        self.redis.rpush(self.wait_key, task_info)

        # 尝试执行任务
        self._exec()

    def _exec(self):
        # 如果当前并发任务数量小于最大并发数，并且等待队列不为空
        while (
            self.redis.llen(self.concur_key) < self.concur_size
            and self.redis.llen(self.wait_key) > 0
        ):
            # 从等待队列中取出任务，并添加到并发队列
            task_info = self.redis.lpop(self.wait_key)
            self.redis.rpush(self.concur_key, task_info)

            # 这里需要调用真正的任务执行逻辑
            # 注意：实际任务执行逻辑需要在应用程序中处理，这里仅演示队列管理
            print(f"Executing task: {task_info}")

    def pop(self, _trigger_id: str):
        # 移除已完成的任务，此处简化处理
        # 实际上需要更复杂的逻辑来确保只移除特定的任务
        self.redis.lrem(self.concur_key, 1, _trigger_id)
        self._exec()


taskqueue = RedisTaskQueue(
    settings.redis_host, settings.redis_port, "concur", "wait", 3
)

rate_limiter = RateLimiter(
    capacity=1, rate=settings.midjourney_rate_limit, refill_time=0.3
)


def get_rate_limiter():
    return rate_limiter


async def get_redis_cache() -> Generator[redis.Redis, None, None]:
    """
    https://redis.readthedocs.io/en/stable/examples/asyncio_examples.html

    :return:
    """
    pool = redis.ConnectionPool.from_url(
        str(settings.redis_dsn),
        decode_responses=True,
        health_check_interval=2,
        retry_on_timeout=True,
        max_connections=10,
    )
    async with redis.Redis.from_pool(pool) as r:
        # async with redis.Redis(connection_pool=pool) as r:  # deprecated
        yield r


def get_redis_cache_sync() -> Generator[redis_sync.Redis, None, None]:
    """
    :return:
    """
    pool = redis_sync.ConnectionPool.from_url(
        str(settings.redis_dsn),
        decode_responses=True,
        health_check_interval=2,
        retry_on_timeout=True,
        max_connections=10,
    )
    with redis_sync.Redis(connection_pool=pool) as r:
        yield r
