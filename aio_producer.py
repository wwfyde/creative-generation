import asyncio
import json

import aio_pika

from app import settings


async def main() -> None:
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    print(connection.connected)
    async with connection:
        routing_key = settings.texture_generation_queue

        channel = await connection.channel()

        message = {
            "task_id": "",
            "sub_task_id": "",
            "task_type": "TEXTURE",
            "data": {
                "request_id": 4356744388511,
                "texture_id": 4,
                "prompt": "随机, 蓝色背景",
                "config": {"batch_size": 4},
                "substitution": {
                    # "subject": "a girl"
                    # "subject": "樱花, 日式, 山海纹, 富士山"
                },
                "parameter": {
                    "aspect": "1:1",
                    "tile": True,
                    # "sref": "https://s.mj.run/uNNgfOox2LY",
                    # "sw": 1000
                },
                "tags": [""],
            },
        }
        exchange = await channel.declare_exchange(
            settings.rabbitmq_exchange, type=aio_pika.ExchangeType.TOPIC, durable=True
        )
        queue = await channel.declare_queue(
            settings.texture_generation_queue, durable=True
        )
        await queue.bind(exchange, routing_key)
        await exchange.publish(
            aio_pika.Message(body=json.dumps(message).encode()),
            routing_key=routing_key,
        )
        print()


if __name__ == "__main__":
    asyncio.run(main())
