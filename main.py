import os
import re
import requests
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# ============ YOUR SETTINGS ============
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
SMARTBET_KEY = os.getenv("SMARTBET_KEY", "bcbwb-4d65eeb3-05af-4eb2-8cc7-6216f6622d22")
STAKE = os.getenv("STAKE", "5")
SPORT = "SOCCER"
SOURCE = "smb.Vantage08>TelegramAlerts"
BOOK = "PINNACLE"
# ======================================

SMARTBET_URL = "https://smartbet.io/postpick.php"
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Telegram → SmartBet bot is running!"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text
    if "Snore-fest" not in text or "Under 0.5" not in text:
        return

    # Extract event (3rd line)
    lines = text.strip().split("\n")
    event = ""
    for line in lines:
        if "vs" in line or "VS" in line:
            event = line.replace(" vs ", " - ").replace(" VS ", " - ").strip()
            break

    if not event:
        print("⚠️ Event not found in message.")
        return

    # Create SmartBet payload
    payload = {
        "key": SMARTBET_KEY,
        "sport": SPORT,
        "event": event,
        "bet": "UNDER 0.5",
        "odds": "auto",  # SmartBet will use Pinnacle odds
        "stake": STAKE,
        "book": BOOK,
        "source": SOURCE
    }

    try:
        r = requests.post(SMARTBET_URL, json=payload, timeout=10)
        print(f"✅ Sent bet for {event}: {r.text}")
    except Exception as e:
        print(f"❌ Error sending bet: {e}")

def run_telegram_bot():
    app_telegram = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    app_telegram.add_handler(handler)
    app_telegram.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_telegram_bot).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
