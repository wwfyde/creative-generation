import asyncio
import json

import aio_pika
import redis.asyncio as redis
from loguru import logger
from snowflake import Snowflake, SnowflakeGenerator
from sqlalchemy.orm import Session

from app import settings
from app.db import engine
from app.discord_api import handle_imagine_prompt, imagine
from app.models import PatternPreset
from app.schemas import ImaginePrompt
from app.utils import RateLimiter

rate_limiter = RateLimiter(capacity=1, rate=settings.midjourney_rate_limit, refill_time=0.3)


async def process_message_old(message: str):
    print(f" [x] Received {message}")
    try:
        message: dict = json.loads(message)
    except json.JSONDecodeError:
        detail = f" [x] Received message is not json format: {message=}"
        logger.error(detail)
        print(detail)
        return
    message = dict(request_id=1234, data=dict(prompt="hello"))
    # TODO 通过discord_api 发起请求
    # prompt = handle_prompt(message['data']['prompt'])
    prompt = message['data']['prompt']
    # TODO 使用sleep 代替耗时任务
    # await generate(prompt)
    await asyncio.sleep(10)
    print("图像生成完成")
    r = await redis.from_url(settings.redis_dsn.unicode_string())

    for _ in range(60):
        result = await r.get(f'{settings.redis_texture_generation_result}:{message["request_id"]}')
        if result:
            print(result)
            # TODO 将生成结果发送到rabbitmq 队列中
            break
        else:
            ...
            # print(f"从redis获取结果状态: {result=}")
        # await asyncio.sleep(3)
    else:
        logger.error("请求超时, 请检查请求是否成功")
        print("请求超时, 请检查请求是否成功")
    print(f" [x] Done, received: {message}")
    # await asyncio.sleep(3)


async def process_message(message: aio_pika.abc.AbstractIncomingMessage):
    logger.info(f"从消息队列Received获取到消息: {message.body.decode()}")
    async with message.process():

        try:
            # 从消息队列获取任务,并转换为Python dict对象
            # {
            #     "data": {
            #         "config": {
            #             "batch_size": 4
            #         },
            #         "parameter": {
            #             "aspect": "4:3",
            #             "tile": false
            #         },
            #         "prompt": "条形,平滑",
            #         "request_id": "1772855157141704704",
            #         "substitution": {
            #             "subject": ""
            #         },
            #         "tags": [],
            #         "texture_id": "1"
            #     },
            #     "sub_task_id": "1772855157112344578",
            #     "task_id": "1772844263187845120",
            #     "task_type": "TEXTURE"
            # }
            task_dict: dict = json.loads(message.body.decode())
        except json.JSONDecodeError:
            detail = f" [x] Received message is not json format: {task_dict=}"
            logger.error(detail)
            print(detail)
            return

        with Session(engine) as session:
            # 根据风格获取纹理配置
            texture = session.get(PatternPreset, task_dict['data']['texture_id'])
            default = dict(
                default_prompt=', '.join(texture.prompt),
                instructions=texture.instructions,
                default_parameter=texture.parameters
            )
            # 参数翻译
            # TODO 增加避免中文
            # for key, value in task_dict['substitution'].items():
            #     logger.debug(f"{key=}, {value=}")
            #     value = await translate_by_azure(value, settings.azure_api_instructions)
            #     logger.debug(f"{key=}, {value=}")
            #     task_dict['substitution'][key] = value

            # 参数置换,
            # s = Template(texture_prompt)
            # s.
            # prompt = texture_prompt.format(**task_dict['data']['substitution'])
            # logger.debug(f"参数置换后的提示词: {prompt}")
            # 参数组装
        # 翻译

        # 将 参数置换后的提示词作为Discord Midjourney /imagine Prompt 的一部分
        # task_dict['data']['prompt'] = prompt
        # 参数校验
        imagine_prompt = ImaginePrompt(**task_dict['data'], **default)

        # task = ImaginePrompt(request_id=task_dict['request_id'], **task_dict['data'])
        # 处理提示词
        prompt = await handle_imagine_prompt(imagine_prompt)
        # 速率限制, 最高1Command/3s
        logger.info(f"discord command 消息体: {prompt=}")
        # TODO 将提示词记录到数据库
        await rate_limiter.wait()

        # TODO 使用sleep 代替耗时任务
        test = settings.test
        print(test)
        if test:
            logger.warning("当前处于测试状态")
            await asyncio.sleep(10)
        else:
            # 生成随机数 epoch 纪元参考自discord
            sf = Snowflake.parse(1225001209962692608, 1420070400000)
            gen = SnowflakeGenerator.from_snowflake(sf)
            nonce = str(next(gen))
            logger.info(
                f"Send imagine task to midjourney bot(discord channel). "
                f"channel_id: {settings.channel_id}, request_id: {imagine_prompt.request_id}, nonce: {nonce}")

            await imagine(prompt, nonce)

        print("图像生成完成")
        # r = await redis.from_url(settings.redis_dsn.unicode_string())
        #
        # for _ in range(60):
        #     result = await r.get(f'{settings.redis_texture_generation_result}:{task_dict["data"]["request_id"]}')
        #     if result:
        #         print(f"确认结果:{result}")
        #         # TODO 将生成结果发送到rabbitmq 队列中
        #
        #         # 消息处理完毕后手动确认, 从队列中删除
        #         # await message.ack()
        #         break
        #     else:
        #         # TODO 将任务标记会失败 并清除
        #         # await message.reject(requeue=True)
        #         # await message.nack(requeue=True)
        #
        #         ...
        #
        #         # print(f"从redis获取结果状态: {result=}")
        #     # await asyncio.sleep(3)
        # else:
        #     logger.error(f"请求超时, 请检查请求是否成功")
        #     # await message.reject(requeue=True)
        #     # raise asyncio.TimeoutError(f"请求超时, 请检查请求是否成功")
        # print(f" [x] Done, received: {task_dict}")
        # # await asyncio.sleep(3)


async def main() -> None:
    conn = await aio_pika.connect_robust(settings.rabbitmq_url, heartbeat=60)
    async with conn:
        channel = await conn.channel()

        await channel.declare_exchange(settings.rabbitmq_exchange, type=aio_pika.ExchangeType.TOPIC, durable=True)
        await channel.set_qos(prefetch_count=settings.prefetch_count)
        queue = await channel.declare_queue(settings.texture_generation_queue, durable=True)
        await queue.bind(settings.rabbitmq_exchange, settings.texture_generation_queue)
        logger.info(f'开始消费队列: {settings.texture_generation_queue}')
        await queue.consume(process_message)
        try:
            await asyncio.Future()
        finally:
            await conn.close()


if __name__ == '__main__':
    asyncio.run(main())
