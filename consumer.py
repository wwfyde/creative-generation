import json
import time

import pika
import redis
from loguru import logger

from app import settings
from app.discord_api import imagine


def callback(ch, method, properties, body):
    """
    消息接收到后的回调函数
    :param ch:
    :param method:
    :param properties:
    :param body:
    :return:
    """
    # TODO 解析队列信息
    print(f" [x] Received {body.decode()}")
    try:
        message: dict = json.loads(body.decode())
    except json.JSONDecodeError as exc:
        logger.error(f" [x] Received message is not json format: {body.decode()}")
        print(f" [x] Received message is not json format: {body.decode()}")

        ch.basic_ack(delivery_tag=method.delivery_tag)
        return
    message = dict(request_id=1234, data=dict(prompt="hello"))

    # TODO 通过discord_api 发起请求
    # prompt = handle_prompt(message['data']['prompt'])
    prompt = message['data']['prompt']
    imagine(prompt)
    r = redis.from_url(settings.redis_dsn.unicode_string())

    for _ in range(60):
        result = r.get(f'{settings.redis_texture_generation_result}:{message["request_id"]}')
        if result:
            print(result)
            # TODO 将生成结果发送到rabbitmq 队列中
            # break
        time.sleep(3)
    else:
        logger.error(f"请求超时, 请检查请求是否成功")
        print(f"请求超时, 请检查请求是否成功")
    print(f" [x] Done, received: {message}")
    ch.basic_ack(delivery_tag=method.delivery_tag)


def worker():
    parameters = pika.URLParameters(settings.rabbitmq_url)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.queue_declare(queue=settings.texture_generation_queue, durable=True)
    print(' [*] Waiting for messages. To exit press CTRL+C')
    # 控制并发量
    channel.basic_qos(prefetch_count=1)
    logger.info(f"当前并发量: {settings.concurrency_limit}")
    channel.basic_consume(queue=settings.texture_generation_queue, on_message_callback=callback)

    channel.start_consuming()


def main():
    # for i in range(settings.concurrency_limit):
    #     t = threading.Thread(target=worker)
    #     t.start()
    worker()


if __name__ == '__main__':
    main()
