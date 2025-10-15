import os
import logging
import requests
import asyncio
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Logging setup ---
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Load environment variables ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
IFTTT_URL = os.getenv("IFTTT_URL")

if not BOT_TOKEN or not IFTTT_URL:
    raise Exception("❌ Missing environment variables! Please set BOT_TOKEN and IFTTT_URL in Render.")

# --- Flask app ---
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Telegram ↔ IFTTT Bot is running!", 200

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "OK", 200

# --- Telegram bot handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hello! Send me your betting alert message and I’ll forward it to IFTTT.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_id = update.message.chat.id
    logger.info(f"Received message from {chat_id}: {text}")

    # Extract event and bet from message like "Football: Arsenal vs Chelsea - Over 2.5"
    sport = "Football"
    event = ""
    bet = ""

    if ":" in text:
        parts = text.split(":", 1)
        sport = parts[0].strip()
        remaining = parts[1].strip()
        if "-" in remaining:
            event, bet = remaining.split("-", 1)
            event = event.strip()
            bet = bet.strip()
        else:
            event = remaining

    payload = {
        "value1": event,
        "value2": bet,
        "value3": sport
    }

    try:
        response = requests.post(IFTTT_URL, json=payload, timeout=10)
        if response.status_code == 200:
            await update.message.reply_text(f"✅ Sent to IFTTT!\n\nEvent: {event}\nBet: {bet}")
        else:
            await update.message.reply_text(f"⚠️ IFTTT error: {response.status_code}")
    except Exception as e:
        logger.error(f"Error sending to IFTTT: {e}")
        await update.message.reply_text("❌ Couldn’t reach IFTTT.")

# --- Telegram bot setup ---
application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# --- Run bot with webhook ---
if __name__ == "__main__":
    async def setup_webhook():
        bot = Bot(token=BOT_TOKEN)
        webhook_url = f"https://telegram-ifttt-bot.onrender.com/{BOT_TOKEN}"
        await bot.set_webhook(url=webhook_url)
        logger.info(f"🌐 Webhook set to {webhook_url}")

    asyncio.run(setup_webhook())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
