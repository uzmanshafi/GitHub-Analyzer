from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters
)
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

import re
from analyzer import fetch_github_user, fetch_user_repos, compute_github_score


class BotController:
    def __init__(self, token, github_token=None):
        self.token = token
        self.github_token = github_token
        # Create the Application (replaces Updater in old versions)
        self.application = ApplicationBuilder().token(self.token).build()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handler for /start command.
        """
        welcome_text = (
            "Welcome to the GitHub Analyzer Bot! "
            "Send me a GitHub username or profile link "
            "and I'll check how authentic the account seems."
        )
        await update.message.reply_text(welcome_text)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handler for /help command.
        """
        help_text = (
            "To use this bot, just type the GitHub username or paste a GitHub profile URL.\n"
            "For example:\n"
            "`octocat`\n"
            "or\n"
            "`https://github.com/octocat`"
        )
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

    async def analyze_github_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handler for any text message that might contain a GitHub username or link.
        """
        message_text = update.message.text.strip()

        # Extract the username from a GitHub URL or treat the message as the username
        pattern = r'github\.com/([^/]+)$'
        match = re.search(pattern, message_text)
        if match:
            username = match.group(1)
        else:
            username = message_text

        # Fetch user data
        user_data = fetch_github_user(username, token=self.github_token)
        if not user_data or user_data.get("message") == "Not Found":
            await update.message.reply_text("Sorry, I couldn't find that GitHub user.")
            return

        # Fetch repos
        repos_data = fetch_user_repos(username, token=self.github_token)

        # Compute score
        score = compute_github_score(user_data, repos_data)

        # Construct response
        response = (
            f"**GitHub User**: {user_data['login']}\n"
            f"**Profile**: {user_data['html_url']}\n"
            f"**Public Repos**: {len(repos_data)}\n\n"
            f"**Authenticity Score**: {score}/100"
        )

        await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)

    def setup_handlers(self):
        """
        Register command handlers and message handlers.
        """
        # /start command
        self.application.add_handler(CommandHandler("start", self.start_command))

        # /help command
        self.application.add_handler(CommandHandler("help", self.help_command))

        # Message Handler for plain text (excluding commands)
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.analyze_github_message)
        )

    def run_bot(self):
        """
        Set up handlers and run the bot via polling.
        """
        self.setup_handlers()
        self.application.run_polling()
        print("Bot is running... Press Ctrl+C to stop.")
