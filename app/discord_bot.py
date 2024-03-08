import re

import discord
from discord import Message
from discord.ext import commands
from loguru import logger
from redis import asyncio as redis

from app.utils import download_image
from app.worker import background_task
from main import settings

intents = discord.Intents.default()
# intents = discord.Intents.all()  # 获取所有权限会报错
intents.message_content = True
# Bot 是Discord.Client的一个子类, 因此直接像Client一样传入proxy='proxy_url'即可
bot = commands.Bot(command_prefix='!', intents=intents, proxy=settings.proxy_url)


@bot.command()
async def ping(ctx):
    await ctx.send('pong')


@bot.event
async def on_ready():
    logger.debug(f"Logged in as {bot.user} (ID: {bot.user.id})")
    logger.success(f"Logged in as {bot.user} (ID: {bot.user.id})")


@bot.event
async def on_message(message: Message):
    # 如果消息是由机器人发送的, 则忽略
    # we don't want the bot to  reply to itself
    if message.author.id == bot.user.id:
        logger.debug(f"来自机器人: {bot.user}的消息")
        return
    logger.info(f"{message.author} sent a message: {message.content}")
    logger.debug(f"{message.author} sent a message: {message.content}")
    logger.debug(f"{message.attachments=}")

    # 处理图像附件
    for attachment in message.attachments:

        if attachment.content_type.startswith('image'):
            # 保持图像并分割
            await download_image(attachment.url, settings.project_dir.joinpath('assets'), attachment.filename,
                                 is_split=True)
            logger.debug(f"{attachment.content_type=}, {attachment.filename=}, {attachment.size=}, "
                         f"{attachment.height=}, {attachment.width=}, {attachment.proxy_url=}")
        logger.debug(f"{attachment.url=}, {attachment.description=}, {attachment.filename=}, {attachment.size=}, "
                     f"{attachment.height=}, {attachment.width=}, {attachment.proxy_url=}")
    # 通过 - 字符split message.content
    prompt = message.content.split(' - ')[0].replace("*", "")
    logger.debug(f"{prompt=}")

    # 监听放大信息
    match = re.search(r'Upscaled ', message.content)
    if match:
        logger.info("Upscaled image")
        for attachment in message.attachments:
            if attachment.content_type.startswith('image'):
                logger.info(f"Downloading image {attachment.filename}")
                await download_image(attachment.url, settings.project_dir.joinpath('assets'), attachment.filename)
    match = re.search(r'Image #([1-4])', message.content)
    if match:
        number = match.group(1)
        logger.info(f"Image number {number}")
        for attachment in message.attachments:
            if attachment.content_type.startswith('image'):
                logger.info(f"Downloading image {attachment.filename}, {number=}")
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
