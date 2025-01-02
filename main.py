import os
from dotenv import load_dotenv
from tg_bot import BotController

if __name__ == "__main__":
    # Load environment variables from .env
    load_dotenv()

    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

    # Initialize and run the bot
    bot_controller = BotController(token=TELEGRAM_BOT_TOKEN, github_token=GITHUB_TOKEN)
    bot_controller.run_bot()
