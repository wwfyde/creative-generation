import asyncio
from datetime import datetime

from app.utils import RateLimiter


async def main():
    rate_limiter = RateLimiter(capacity=1, rate=0.1, refill_time=0.1)

    async def task(task_id):
        await rate_limiter.wait()
        print(f"Task {task_id} is running at {datetime.now()}")

    tasks = [task(i) for i in range(10)]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
