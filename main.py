import os
import json
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import requests

# === CONFIGURATION ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
SMARTBET_KEY = os.getenv("SMARTBET_KEY")
SPORT = os.getenv("SPORT", "SOCCER")
STAKE = os.getenv("STAKE", "5")
BOOK = os.getenv("BOOK", "PINNACLE")
SOURCE = os.getenv("SOURCE", "Telegram>Alerts")

SMARTBET_URL = "https://smartbet.io/postpick.php"

# === FLASK HEALTH CHECK ===
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running", 200

# === PARSE TELEGRAM ALERT ===
def parse_alert(message_text):
    lines = message_text.split("\n")
    event = None
    bet = None

    # Bet type
    for line in lines:
        if line.lower().startswith("bet :"):
            bet = line.split(":")[1].strip().upper()  # e.g., UNDER 0.5, 1, X, 2, HOME +1.5
            break

    # Event
    for line in lines:
        if " vs " in line.lower():
            event = line.strip().replace(" vs ", " - ").replace(" VS ", " - ")
            break

    return {"event": event or "Unknown Event", "bet": bet or "UNKNOWN"}

# === SEND PICK TO SMARTBET.IO ===
def send_to_smartbet(event, bet):
    payload = {
        "key": SMARTBET_KEY,
        "sport": SPORT,
        "event": event,
        "bet": bet,
        "odds": "0.0",   # Let SmartBet.io use Pinnacle live odds
        "stake": STAKE,
        "book": BOOK,
        "source": SOURCE
    }
    try:
        response = requests.post(SMARTBET_URL, json=payload)
        print(f"✅ Sent to SmartBet.io: {json.dumps(payload)}")
        print(f"🔄 Response: {response.text}")
    except Exception as e:
        print(f"❌ Error sending to SmartBet.io: {e}")

# === TELEGRAM HANDLER ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text:
        return

    # Only process messages containing a bet
    if "Bet :" in text:
        alert_data = parse_alert(text)
        send_to_smartbet(alert_data["event"], alert_data["bet"])
        await update.message.reply_text(f"✅ Pick sent to SmartBet.io!")

# === START FLASK + TELEGRAM BOT ===
if __name__ == '__main__':
    # Run Flask in a background thread
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))).start()

    # Run Telegram bot in the main thread
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Telegram bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
