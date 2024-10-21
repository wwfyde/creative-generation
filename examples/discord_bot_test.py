# This example requires the 'message_content' intent.

import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=">", intents=intents)


@bot.command()
async def ping(ctx):
    await ctx.send("pong")


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content == "ping":
        print("recieved ping")
        ...
        # await message.channel.send('pong')
    print(message.content)

    # 处理命令并发送消息
    await bot.process_commands(message)


if __name__ == "__main__":
    bot.run("MTIwOTczMTkxMzI4MDAwNDEzOA.GlC2NK._ojHyMxThSuQuqJOtiY47x90_nTzvRwnjDaGfQ")
