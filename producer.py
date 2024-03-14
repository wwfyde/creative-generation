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

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost', port='5672', ))  # 创建连接对象
channel = connection.channel()  # 创建信道
channel.queue_declare(queue=settings.texture_generation_queue, durable=True)  # 声明队列

while True:
    request_id = uuid.uuid4().int
    message = {
        "request_id": request_id,
        'texture_id': 1,
        'substitution': {'subject': '老虎'},
        'parameter': {'aspect': '4:3', 'tile': True},
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
