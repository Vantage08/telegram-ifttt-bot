import os
import logging
from flask import Flask
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import requests

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SMARTBET_KEY = os.getenv("SMARTBET_KEY")
SPORT = os.getenv("SPORT", "SOCCER")
BET_TYPE = os.getenv("BET_TYPE", "UNDER 0.5")
STAKE = os.getenv("STAKE", "5")
BOOK = os.getenv("BOOK", "PINNACLE")
SOURCE = os.getenv("SOURCE", "smb.Vantage08>TelegramAlerts")

# Flask app (for Render web service)
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Telegram–SmartBet Bot is running!"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggered when a Telegram message is received."""
    if not update.message or not update.message.text:
        return

    message_text = update.message.text.strip()
    logger.info(f"Received message: {message_text}")

    # Simple extraction (for now we just send a fixed bet to SmartBet)
    payload = {
        "key": SMARTBET_KEY,
        "sport": SPORT,
        "event": "AUTO-DETECTED EVENT",
        "bet": BET_TYPE,
        "odds": "1.90",
        "stake": STAKE,
        "book": BOOK,
        "source": SOURCE
    }

    try:
        response = requests.post("https://smartbet.io/postpick.php", json=payload)
        logger.info(f"SmartBet response: {response.text}")
        await update.message.reply_text("✅ Bet sent to SmartBet.io!")
    except Exception as e:
        logger.error(f"Failed to send bet: {e}")
        await update.message.reply_text("❌ Failed to send bet to SmartBet.io.")

def start_bot():
    """Start the Telegram bot."""
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("🚀 Starting Telegram bot polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    import threading

    # Run the Telegram bot in a background thread
    threading.Thread(target=start_bot, daemon=True).start()

    # Run Flask web server for Render
    app.run(host="0.0.0.0", port=10000)
