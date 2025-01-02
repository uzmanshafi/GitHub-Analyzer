import os
from dotenv import load_dotenv
from tg_bot import BotController

if __name__ == "__main__":
    load_dotenv()

    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

    bot = BotController(token=TELEGRAM_BOT_TOKEN, github_token=GITHUB_TOKEN)
    bot.run_bot()
