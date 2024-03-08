import redis

redis_client = redis.Redis()


async def consumer():
    while True:
        ...
