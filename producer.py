"""
producer:
https://www.rabbitmq.com/tutorials/tutorial-one-python.html
"""
import json
import time
import uuid

import pika

from app import settings


# credentials = pika.PlainCredentials('', 'password')
# 建立连接
def main():
    connection = pika.BlockingConnection(pika.URLParameters(settings.rabbitmq_url))
    # connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost', port='5672', ))  # 创建连接对象
    channel = connection.channel()  # 创建信道
    channel.queue_declare(queue=settings.texture_generation_queue, durable=True)  # 声明队列

    while True:
        request_id = uuid.uuid4().int
        message = {
            "request_id": request_id,
            'texture_id': 1,
            'substitution': {'subject': 'a girl'},
            'parameter': {'aspect': '4:3', 'tile': True},
        }
        message = {
            "task_id": "",
            "sub_task_id": "",
            "task_type": "TEXTURE",
            "data": {
                "request_id": 22435678888,
                "texture_id": 1,
                "prompt": "",
                "config": {
                    "batch_size": 4
                },
                "substitution": {
                    "subject": "樱花, 日式, 山海纹, 富士山"
                },
                "parameter": {
                    "aspect": "4:3",
                    "tile": True
                },
                "tags": [""]
            }
        }
        message_str = json.dumps(message)
        channel.basic_publish(exchange='',
                              routing_key=settings.texture_generation_queue,
                              properties=pika.BasicProperties(
                                  delivery_mode=2,  # make message persistent
                                  content_type='application/json',
                                  content_encoding='utf-8',
                              ),
                              body=message_str)
        print(f"[x] sent to {settings.texture_generation_queue} with message {message_str}")

        time.sleep(100)


if __name__ == '__main__':
    main()
