import asyncio

from celery import Celery
from loguru import logger

app = Celery('midjourney-tasks', broker='redis://localhost:6379/0', backend="redis://localhost:6379/0")


@app.task
def add(x, y):
    return x + y


@app.task
async def demo():
    logger.debug("async test")
    await asyncio.sleep(3)
    return "async consumer finished"


@app.task
def background_task(name: str) -> str:
    return f"Hello, {name}! This is a background task."
