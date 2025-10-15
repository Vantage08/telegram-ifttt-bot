import os
import asyncio
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# Load environment variables
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = "https://telegram-ifttt-bot.onrender.com"  # your Render URL (no trailing slash)

# Flask app
app = Flask(__name__)

# Initialize bot and telegram application
bot = Bot(token=TOKEN)
application = Application.builder().token(TOKEN).build()

# --- Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reply when /start is sent."""
    await update.message.reply_text("👋 Hello! Your bot is live and connected successfully!")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Echo any message sent to the bot."""
    user_message = update.message.text
    await update.message.reply_text(f"✅ Received: {user_message}")

# Register handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# --- Flask routes ---

@app.route('/')
def index():
    return "🤖 Telegram bot is running!", 200

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    """Receive updates from Telegram"""
    update = Update.de_json(request.get_json(force=True), bot)
    asyncio.run(application.process_update(update))
    return "OK", 200

# --- Webhook setup ---
async def setup_webhook():
    """Set Telegram webhook asynchronously"""
    await bot.delete_webhook()
    await bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
    print(f"🤖 Webhook set to {WEBHOOK_URL}/{TOKEN}")

# --- Main entry point ---
if __name__ == "__main__":
    asyncio.run(setup_webhook())
    print("🌐 Telegram bot is running on Render...")
    app.run(host="0.0.0.0", port=10000)
