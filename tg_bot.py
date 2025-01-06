import logging
import re
import json
import os
import threading

from urllib.parse import urlparse
from telegram import Update, Chat
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from analyzer import compute_profile_analysis

# Configure logging to STDOUT for platforms like Render
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

SOLANA_WALLET_ADDRESS = "7RGjKAS8Lij9oAihuWcuprYQ7Qu1p674Qf7z8HfLvnXa"

COUNT_FILE = "count.json"
COUNT_LOCK = threading.Lock()

def extract_github_username(text: str) -> str:
    """
    Parses a possible GitHub link and extracts the first path segment after github.com/,
    or returns the raw text if no match.
    """
    parsed = urlparse(text)
    if parsed.netloc and "github.com" in parsed.netloc:
        path_parts = parsed.path.strip("/").split("/")
        if path_parts:
            return path_parts[0]
    else:
        pattern = r"github\.com/([^/]+)"
        match = re.search(pattern, text)
        if match:
            return match.group(1)

    return text.strip()

def load_counts():
    if os.path.exists(COUNT_FILE):
        try:
            with COUNT_LOCK, open(COUNT_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logging.error("Failed to decode JSON from counts.json. Starting with empty counts.")
            return {}
    return {}

def save_counts(counts):
    try:
        with COUNT_LOCK, open(COUNT_FILE, 'w') as f:
            json.dump(counts, f)
    except Exception as e:
        logging.error(f"Failed to save counts to {COUNT_FILE}: {e}")
        
        
class BotController:
    def __init__(self, token, github_token=None):
        self.token = token
        self.github_token = github_token
        self.application = ApplicationBuilder().token(self.token).build()
        self.scan_counts = load_counts()
        logging.info("BotController initialized with token and GitHub token.")

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """
        Global error handler for logging exceptions.
        """
        logging.error("Exception in update:", exc_info=context.error)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /start command. For private chats or group usage.
        """
        logging.info(f"/start command invoked by {update.effective_user.username if update.effective_user else 'Unknown'}")
        welcome_text = (
            "<b>Welcome to the GitHub Analyzer Bot!</b>\n\n"
            "Send me a GitHub username or profile link, and I will check how legit the account is.\n\n"
            "In a group chat, use /analyze &lt;GitHub username or link&gt;.\n\n"
            "This bot was created by @defamed_sol. If you like to show support, "
            f"please donate SOL to <code>{SOLANA_WALLET_ADDRESS}</code>.\n\n"
            "Use /help to see more commands."
        )
        await update.effective_message.reply_text(welcome_text, parse_mode=ParseMode.HTML)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /help command.
        """
        logging.info(f"/help command invoked by {update.effective_user.username if update.effective_user else 'Unknown'}")
        help_text = (
            "<b>How to use this bot</b>:\n\n"
            "• In a group chat:\n"
            "  <code>/analyze octocat</code>\n"
            "  <code>/analyze https://github.com/octocat</code>\n\n"
            "• In a private chat:\n"
            "  Send me a GitHub username or link directly.\n\n"
            "I'll analyze the profile and provide details such as readme depth, commit patterns, "
            "AI/Crypto usage, etc."
        )
        await update.effective_message.reply_text(help_text, parse_mode=ParseMode.HTML)

    async def analyze_group_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handler for the group command: /analyze <GitHub username or link>
        """
        chat = update.effective_chat
        message = update.effective_message

        # If there's no chat or message, we can't proceed
        if not chat or not message:
            logging.info("No chat/message in update, ignoring /analyze command.")
            return

        if chat.type == Chat.PRIVATE:
            logging.info("User tried /analyze in a private chat.")
            await message.reply_text("Please use this command in a group chat.")
            return

        text = message.text.strip() if message.text else ""
        logging.info(f"Group analyze command received: {text}")

        # Capture anything after '/analyze '
        pattern = r"^/analyze\s+(.+)$"
        match = re.match(pattern, text)
        if not match:
            usage_msg = (
                "Usage:\n"
                "/analyze <GitHub username or link>\n\n"
                "Examples:\n"
                "/analyze octocat\n"
                "/analyze https://github.com/octocat"
            )
            await message.reply_text(usage_msg)
            return

        user_input = match.group(1).strip()
        logging.info(f"Extracted user input from group command: {user_input}")

        github_user = extract_github_username(user_input)
        analyzing_msg = await message.reply_text(
            f"Analyzing GitHub user <b>{github_user}</b>... please wait!",
            parse_mode=ParseMode.HTML
        )

        logging.info(f"Starting analysis for {github_user}...")
        result = compute_profile_analysis(github_user, token=self.github_token)
        logging.info(f"Analysis complete for {github_user}.")

        if "error" in result:
            await analyzing_msg.edit_text("❌ User not found or an error occurred.")
            return

        await self._send_analysis_result(update, context, result, editing_msg=analyzing_msg)

    async def analyze_private_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handler for private messages with a GitHub username or link.
        """
        chat = update.effective_chat
        message = update.effective_message

        # Only respond if it's truly a private chat
        if not chat or not message or chat.type != Chat.PRIVATE:
            return

        message_text = message.text.strip()
        logging.info(f"Private text received: {message_text}")

        username = extract_github_username(message_text)
        logging.info(f"Extracted username: {username}")

        analyzing_msg = await message.reply_text(
            f"Analyzing GitHub user <b>{username}</b>... please wait!",
            parse_mode=ParseMode.HTML
        )

        logging.info(f"Starting analysis for {username}...")
        result = compute_profile_analysis(username, token=self.github_token)
        logging.info(f"Analysis complete for {username}.")

        if "error" in result:
            await analyzing_msg.edit_text("❌ User not found or an error occurred.")
            return

        await self._send_analysis_result(update, context, result, editing_msg=analyzing_msg)

    async def _send_analysis_result(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        result: dict,
        editing_msg=None
    ):
        """
        Helper method to format and send the analysis result.
        If editing_msg is provided, we edit that message with the final text.
        Otherwise, we send a new message.
        """
        user_data = result["user_data"]
        score = result["score"]
        warnings = result["warnings"]
        has_ai = result["has_ai"]
        has_crypto = result["has_crypto"]
        score_breakdown = result["score_breakdown"]
        
        github_url = user_data['html_url']
        
        if github_url in self.scan_counts:
            self.scan_counts[github_url] += 1
        else:
            self.scan_counts[github_url] = 1
            
        save_counts(self.scan_counts)
        
        scan_count = self.scan_counts[github_url]

        summary = (
            f"<b>GitHub User</b>: {user_data['login']}\n"
            f"<b>Profile</b>: {user_data['html_url']}\n"
            f"<b>Public Repos</b>: {len(result['repo_data'])}\n\n"
            f"<b>Score</b>: {score}/100\n"
        )

        # Detailed breakdown of scores
        breakdown_text = (
            "🔹 <b>Breakdown</b>:\n"
            f"• Account Age Points: {score_breakdown['account_age_points']}\n"
            f"• Readme Depth Points: {score_breakdown['readme_points']}\n"
            f"• Commit Frequency Points: {score_breakdown['commit_points']}\n"
            f"• PR/Issues Points: {score_breakdown['pr_issues_points']}\n"
            f"• Profile Bio/Blog Points: {score_breakdown['profile_bio_blog_points']}\n"
            f"• AI/Crypto Points: {score_breakdown['ai_crypto_points']}\n"
        )
        summary += breakdown_text + "\n"

        # AI/Crypto mention
        if has_ai or has_crypto:
            ai_crypto_note = []
            if has_ai:
                ai_crypto_note.append("🧠 <b>Detected AI-related libraries.</b>")
            if has_crypto:
                ai_crypto_note.append("₿ <b>Detected Crypto/Blockchain references.</b>")
            summary += "\n".join(ai_crypto_note) + "\n\n"
        else:
            summary += "❓ <b>No specific AI or crypto references detected.</b>\n\n"

        # Warnings
        if warnings:
            summary += "<b>Warnings</b>:\n"
            for w in warnings:
                summary += f"⚠️ {w}\n"
            summary += "\n"

        # ASCII bar chart
        summary += f"<pre>{result['ascii_lang_chart']}</pre>\n"

        # Social links
        blog = result.get("blog", None)
        twitter_user = result.get("twitter_user", None)
        if blog or twitter_user:
            summary += "<b>Social Links Found</b>:\n"
            if blog:
                summary += f"🔗 Website/Blog: {blog}\n"
            if twitter_user:
                summary += f"🐦 Twitter: @{twitter_user}\n"
                
        # Scan Count
        summary += f"\n👁️ **Scanned {scan_count} times**"
        
        # Disclaimer
        disclaimer = (
            "\n⚠️ <i>Please note:</i> The bot isn’t always 100% accurate and I can’t be held responsible "
            "for any decisions made based on its analysis. Always do your own research before making any investments."
        )
        summary += disclaimer

        final_text = summary

        if editing_msg:
            await editing_msg.edit_text(final_text, parse_mode=ParseMode.HTML)
        else:
            await update.effective_message.reply_text(final_text, parse_mode=ParseMode.HTML)

    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("analyze", self.analyze_group_command))
        self.application.add_handler(
            MessageHandler(
                filters.TEXT & filters.ChatType.PRIVATE & ~filters.COMMAND,
                self.analyze_private_text
            )
        )
        self.application.add_error_handler(self.error_handler)

    def run_bot(self):
        self.setup_handlers()
        logging.info("Starting the bot via polling...")
        self.application.run_polling()
        logging.info("Bot has stopped polling. Exiting.")
        print("Bot is running... Press Ctrl+C to stop.")
