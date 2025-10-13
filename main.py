import os
import re
import json
import threading
import requests
from flask import Flask
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# === CONFIGURATION ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
IFTTT_WEBHOOK_URL = os.getenv(
    "IFTTT_WEBHOOK_URL",
    "https://maker.ifttt.com/trigger/telegram_alert/with/key/c6QsqQqCIl9LzH6X2Oo04yAbYvsAfrCLP44qy9_sCt2"
)
SMARTBET_KEY = os.getenv("SMARTBET_KEY", "bcbwb-4d65eeb3-05af-4eb2-8cc7-6216f6622d22")
SPORT = os.getenv("SPORT", "SOCCER")
STAKE = os.getenv("STAKE", "5")
BOOK = os.getenv("BOOK", "PINNACLE")
SOURCE = os.getenv("SOURCE", "smb.Vantage08>TelegramAlerts")

# === FLASK HEALTH CHECK ===
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot running via IFTTT bridge", 200

# === PARSER ===
def parse_alert(message_text):
    lines = message_text.split("\n")

    event = None
    odds = None
    bet = "UNDER 0.5"

    for line in lines:
        if " vs " in line or " VS " in line:
            event = line.strip()
            break

    for line in lines:
        match = re.findall(r"\d+\.\d+", line)
        if len(match) == 2:
            odds = match[1]
            break

    return {
        "event": event or "Unknown Event",
        "bet": bet,
        "odds": odds or "0.0"
    }

# === SEND TO IFTTT ===
def send_to_ifttt(event, bet, odds):
    payload = {
        "key": SMARTBET_KEY,
        "sport": SPORT,
        "event": event,
        "bet": bet,
        "odds": odds,
        "stake": STAKE,
        "book": BOOK,
        "source": SOURCE
    }

    data = {"value1": json.dumps(payload)}

    try:
        response = requests.post(IFTTT_WEBHOOK_URL, json=data)
        print(f"\n✅ Sent to IFTTT: {json.dumps(payload, indent=2)}")
        print(f"🔄 IFTTT response: {response.text}\n")
    except Exception as e:
        print(f"❌ Error sending to IFTTT: {e}")

# === TELEGRAM HANDLER ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if not text:
        return

    if "Over/Under 0.50 Odds" in text:
        alert_data = parse_alert(text)
        send_to_ifttt(alert_data["event"], alert_data["bet"], alert_data["odds"])
        await update.message.reply_text("✅ Bet forwarded to IFTTT → SmartBet.io")

# === TELEGRAM BOT RUNNER ===
def run_telegram_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Telegram → IFTTT bridge running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

# === FLASK SERVER (for Render health check) ===
if __name__ == '__main__':
    threading.Thread(target=run_telegram_bot).start()
    app.run(host='0.0.0.0', port=10000)
