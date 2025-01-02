import os
from dotenv import load_dotenv
from tg_bot import BotController

if __name__ == "__main__":
    load_dotenv()  # load variables from .env

    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

    bot_controller = BotController(token=TELEGRAM_BOT_TOKEN, github_token=GITHUB_TOKEN)
    bot_controller.run_bot()
