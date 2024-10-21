import asyncio
import time

from celery import Celery
from loguru import logger
from websockets.sync.client import connect

app = Celery(
    "worker", broker="redis://localhost:6379/0", backend="redis://localhost:6379/0"
)


@app.task(name="sum")
def add(x, y):
    logger.debug(f"add: {x} + {y}")
    return x + y


@app.task
async def demo():
    logger.debug("async test")
    await asyncio.sleep(3)
    return "async consumer finished"


@app.task
def background_task(name: str) -> str:
    time.sleep(15 * 16)
    return f"Hello, {name}! This is a background task."


# @app.task(bind=True)
#


@app.task
def send_to_ws():
    with connect("ws://localhost:8000/api/ws") as websocket:
        websocket.send("Hello, world!")
