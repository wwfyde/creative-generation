from app.config import settings
from app.discord_bot import bot

# bot.run(settings.bot_token)

if __name__ == "__main__":
    bot.run(settings.bot_token, root_logger=True)
