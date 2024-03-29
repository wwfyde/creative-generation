import json
import re

import aio_pika
import discord
import redis.asyncio as redis
from discord import Message
from discord.ext import commands
from loguru import logger
from websockets.sync.client import connect

from app.utils import download_image, download_image_to_oss
from app.worker import background_task
from main import settings

intents = discord.Intents.all()
# intents = discord.Intents.all()  # 获取所有权限会报错
intents.message_content = True
# Bot 是Discord.Client的一个子类, 因此直接像Client一样传入proxy='proxy_url'即可
bot = commands.Bot(command_prefix='>', intents=intents, proxy=settings.proxy_url)


@bot.command()
async def ping(ctx):
    await ctx.send('pong')


@bot.event
async def on_ready():
    # logger.debug(f"Logged in as {bot.user} (ID: {bot.user.id})")
    logger.success(f"Logged in as {bot.user} (ID: {bot.user.id})")


@bot.event
async def on_message(message: Message):
    # 如果消息是由机器人发送的, 则忽略
    # we don't want the bot to  reply to itself
    if message.author.id == bot.user.id:
        logger.debug(f"来自机器人: {bot.user}的消息")
        return
    logger.info(f"{message.author} sent a message: {message.content}")

    # 处理图像附件
    # for attachment in message.attachments:
    #
    #     if attachment.content_type.startswith('image'):
    #         # 保持图像并分割
    #         await download_image(attachment.url, settings.project_dir.joinpath('assets'), attachment.filename,
    #                              is_split=True)
    #         logger.debug(f"{attachment.content_type=}, {attachment.filename=}, {attachment.size=}, "
    #                      f"{attachment.height=}, {attachment.width=}, {attachment.proxy_url=}")
    #     logger.debug(f"{attachment.url=}, {attachment.description=}, {attachment.filename=}, {attachment.size=}, "
    #                  f"{attachment.height=}, {attachment.width=}, {attachment.proxy_url=}")
    # 通过 - 字符split message.content
    # prompt = message.content.split(' - ')[0].replace("*", "")
    # logger.debug(f"{prompt=}")

    # 监听 以fast或(turbo)结尾的消息
    match = re.search(r' \(fast\)$| \(turbo\)$', message.content)
    if match:
        # 获取message_id message_hash 等
        message_id = message.id
        message_hash = message.attachments[0].id
        # TODO 将数据发送到队列
        match = re.search(rf"{settings.prompt_prefix}(\d+){settings.prompt_suffix}", message.content)
        if match:
            request_id = match.group(1)
            image_urls = []
            attachments_meta = []
            for attachment in message.attachments:
                # 将图片上传到阿里云OSS并写入数据库
                attachments_meta.append(dict(
                    id=attachment.id,
                    width=attachment.width,
                    height=attachment.height,
                    filename=attachment.filename,
                    url=attachment.url,
                    contentType=attachment.content_type
                ))
                if attachment.content_type.startswith('image'):
                    # 将图片上传到阿里云OSS
                    attachment_image_urls = await download_image_to_oss(attachment.url, attachment.filename,
                                                                        is_split=True, request_id=request_id)
                    image_urls.extend(attachment_image_urls)

            # TODO 将生成结果发送到rabbitmq队列
            body = {
                "code": 200,
                "data": {
                    "images": image_urls,
                    "requestId": request_id,
                    "messageId": message_id,
                    "messageHash": message_hash,
                    "messageContent": message.content,
                    "attachments": attachments_meta
                }
            }
            body_str = json.dumps(body)
            connection = await aio_pika.connect_robust(
                settings.rabbitmq_url
            )
            async with connection:
                route_key = settings.texture_generation_result_queue
                channel = await connection.channel()
                exchange = await channel.declare_exchange(settings.rabbitmq_exchange,
                                                          type=aio_pika.ExchangeType.TOPIC,
                                                          durable=True)
                queue = await channel.declare_queue(route_key, durable=True)
                await queue.bind(exchange, route_key)

                await exchange.publish(
                    aio_pika.Message(body=body_str.encode()),
                    routing_key=route_key
                )
                logger.debug(f"将{request_id}生成结果发送到RabbitMQ: {body_str}")
            # TODO 将数据发送到redis

            r = await redis.from_url(settings.redis_dsn.unicode_string())

            await r.set(f"{settings.redis_texture_generation_result}:{request_id}", body_str)
            logger.info(f"将{request_id=}生成结果发送到redis: {body_str=}")
            await r.close()



        else:
            # 过滤
            pass

            ...

    return
    # 监听放大信息 Upscale(Subtle), Upscale(Creative)
    match = re.search(r'Upscaled ', message.content)
    if match:
        logger.info("Upscaled image")
        for attachment in message.attachments:
            if attachment.content_type.startswith('image'):
                logger.info(f"Downloading image {attachment.filename}")
                await download_image(attachment.url, settings.project_dir.joinpath('assets'), attachment.filename)
    # 监听图像选择
    match = re.search(r'Image #([1-4])', message.content)
    if match:
        number = match.group(1)
        logger.info(f"Image number {number}")
        for attachment in message.attachments:
            if attachment.content_type.startswith('image'):
                logger.info(f"Downloading image {attachment.filename}, {number=}")
                await download_image(attachment.url, settings.project_dir.joinpath('assets'), attachment.filename)
    #
    if message.content.startswith('**'):
        logger.debug(f"来自Midjourney Bot 的消息{message.content}")
        if '(fast)' in message.content:
            logger.debug("图像处理完成")
            # 获取图像
            for attachment in message.attachments:
                if attachment.content_type.startswith('image'):
                    logger.debug(f"Downloading image {attachment.filename}")
                    # Image.open(attachment.url)
                    with connect("ws://localhost:8000/api/ws") as websocket:
                        logger.info(f"id: 图像生成完成:{attachment.url} ")
                        # TODO send json message
                        websocket.send(attachment.url)

                    await download_image(attachment.url, settings.project_dir.joinpath('assets'), attachment.filename)

    if message.content.startswith('>'):
        # TODO 接收到消息后逻辑
        logger.debug(f"触发消息内容| {message.content}")
        # 从celery中获取请求到的结果
        result = background_task.delay(message.content[1:])
        image_path = result.get()
        # 将消息发送到Discord
        await message.channel.send(image_path)
        r = await redis.Redis(host=settings.redis_host, port=settings.redis_port, db=settings.redis_db)
        task = await r.lpop('tasks')
        if task:
            await message.channel.send(task)
        else:
            await message.channel.send('No tasks available')
        await bot.process_commands(message)

    # TODO 回调函数
    ...


@bot.event
async def on_message_edit(_, after):
    ...


@bot.event
async def om_message_delete(message: Message):
    ...


@bot.command()
async def add(ctx, left: int, right: int):
    ctx.send(left + right)
