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
from analyzer import (
    fetch_github_user,
    fetch_user_repos,
    compute_github_score
)

SOLANA_WALLET_ADDRESS = "7RGjKAS8Lij9oAihuWcuprYQ7Qu1p674Qf7z8HfLvnXa"

class BotController:
    def __init__(self, token, github_token=None):
        self.token = token
        self.github_token = github_token
        self.application = ApplicationBuilder().token(self.token).build()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handler for /start command.
        Now using HTML formatting.
        """
        welcome_text = (
            "<b>Welcome to the GitHub Analyzer Bot!</b>\n\n"
            "Send me a GitHub username or profile link, and I will check how legit the account is.\n\n"
            "This bot was created by @defamed_sol. If you like to show support for further development, "
            f"please donate some SOLAMIs to <code>{SOLANA_WALLET_ADDRESS}</code>.\n\n"
            "Use /help to see more commands."
        )
        await update.message.reply_text(welcome_text, parse_mode=ParseMode.HTML)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = (
            "<b>How to use this bot</b>:\n"
            "• Just type the GitHub username or paste a GitHub profile URL.<br>"
            "  Example: <code>octocat</code> or <code>https://github.com/octocat</code><br>"
            "• I will fetch data about the account, analyze repos & commit messages, and provide a score.\n\n"
            "<b>Commands</b>:<br>"
            "/start - Start interacting with the bot<br>"
            "/help - Show this help message\n\n"
            "💸 <b>Donations</b>:<br>"
            f"To support this bot, donate SOL to: <code>{SOLANA_WALLET_ADDRESS}</code>"
        )
        await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)

    async def analyze_github_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message_text = update.message.text.strip()

        # Extract username from a GitHub URL or treat as username
        pattern = r'github\.com/([^/]+)$'
        match = re.search(pattern, message_text)
        if match:
            username = match.group(1)
        else:
            username = message_text

        user_data = fetch_github_user(username, token=self.github_token)
        if not user_data or user_data.get("message") == "Not Found":
            await update.message.reply_text("❌ Sorry, I couldn't find that GitHub user.")
            return

        repos_data = fetch_user_repos(username, token=self.github_token)
        analysis_result = compute_github_score(user_data, repos_data, token=self.github_token)

        sub_scores = analysis_result["sub_scores"]
        max_scores = analysis_result["max_scores"]
        final_score = analysis_result["normalized_score"]
        warnings = analysis_result["warnings"]

        # Build sub-score breakdown (using HTML tags)
        breakdown = (
            f"🔹 <b>Account Age</b>: {sub_scores['account_age_score']:.2f}/{max_scores['account_age']}<br>"
            f"🔹 <b>Profile Completeness</b>: {sub_scores['profile_completeness_score']:.2f}/{max_scores['profile_completeness']}<br>"
            f"🔹 <b>Repo Activity</b>: {sub_scores['repo_activity_score']:.2f}/{max_scores['repo_activity']}<br>"
            f"🔹 <b>Community Interaction</b>: {sub_scores['community_interaction_score']:.2f}/{max_scores['community_interaction']}<br>"
            f"🔹 <b>External Consistency</b>: {sub_scores['external_consistency_score']:.2f}/{max_scores['external_consistency']}<br>"
            f"🔹 <b>Readme/Commits</b>: {sub_scores['readme_commit_score']:.2f}/{max_scores['readme_commit']}<br>"
        )

        # Social links if any
        social_links = []
        if user_data.get("blog"):
            social_links.append(f"🔗 Website/Blog: {user_data['blog']}")
        if user_data.get("twitter_username"):
            social_links.append(f"🐦 Twitter: @{user_data['twitter_username']}")

        social_section = "\n".join(social_links) if social_links else "No additional social links found."

        # Warnings
        if warnings:
            warnings_text = "\n".join([f"⚠️ {w}" for w in warnings])
        else:
            warnings_text = "No obvious warnings. 🎉"

        response = (
            f"👤 <b>GitHub User</b>: {user_data['login']}\n"
            f"🌐 <b>Profile</b>: {user_data['html_url']}\n"
            f"📦 <b>Public Repos</b>: {len(repos_data)}\n\n"
            f"{breakdown}\n"
            f"✅ <b>Total Authenticity Score</b>: {final_score}/100\n\n"
            f"<b>Social Links</b>:\n{social_section}\n\n"
            f"<b>Analysis Warnings</b>:\n{warnings_text}\n\n"
            f"💰 <i>If you find this bot helpful, consider donating SOL:</i>\n"
            f"<code>{SOLANA_WALLET_ADDRESS}</code>"
        )

        await update.message.reply_text(response, parse_mode=ParseMode.HTML)

    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.analyze_github_message))

    def run_bot(self):
        self.setup_handlers()
        self.application.run_polling()
        print("Bot is running... Press Ctrl+C to stop.")
