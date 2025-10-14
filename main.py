import os
import re
import json
import requests
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# === CONFIG ===
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Telegram bot token
SMARTBET_KEY = os.getenv("SMARTBET_KEY", "bcbwb-4d65eeb3-05af-4eb2-8cc7-6216f6622d22")
SPORT = os.getenv("SPORT", "SOCCER")
STAKE = os.getenv("STAKE", "5")
BOOK = os.getenv("BOOK", "PINNACLE")
SOURCE = os.getenv("SOURCE", "smb.Vantage08>TelegramAlerts")
SMARTBET_URL = "https://smartbet.io/postpick.php"

WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g. https://telegram-ifttt-bot.onrender.com/webhook

app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)

# === PARSER FUNCTION ===
def parse_alert(message_text):
    """
    Example:
    Bet : Under 0.5
    🇦🇷 Argentina Primera B Metropolitana (17th vs 10th)
    Deportivo Liniers vs Excursionistas
    Over/Under 0.50 Odds:
    2.10 1.67
    """
    lines = message_text.split("\n")
    event, bet, odds = None, None, None

    # Extract Bet type
    for line in lines:
        if "Bet" in line:
            bet_match = re.search(r"Bet\s*[:\-]\s*(.+)", line, re.IGNORECASE)
            if bet_match:
                bet = bet_match.group(1).strip().upper()
                break

    # Extract event (the line with "vs" or "VS")
    for line in lines:
        if " vs " in line.lower():
            event = line.strip().replace(" - ", " vs ").replace("-", " vs ")
            break

    # Extract odds (usually two decimals like "2.10 1.67")
    for line in lines:
        odds_match = re.findall(r"\d+\.\d+", line)
        if len(odds_match) >= 1:
            odds = odds_match[-1]  # last number (usually UNDER)
            break

    return {
        "event": event or "Unknown Event",
        "bet": bet or "UNKNOWN BET",
        "odds": odds or "0.0",
    }

# === SEND TO SMARTBET.IO ===
def send_to_smartbet(event, bet, odds):
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
    try:
        response = requests.post(SMARTBET_URL, json=payload)
        print(f"✅ Sent to SmartBet.io:\n{json.dumps(payload, indent=2)}")
        print(f"🔄 SmartBet.io Response: {response.text}")
    except Exception as e:
        print(f"❌ Error sending to SmartBet.io: {e}")

# === TELEGRAM WEBHOOK HANDLER ===
@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    if update.message and update.message.text:
        message_text = update.message.text
        print(f"📩 Received alert: {message_text}")

        # Parse and send to SmartBet.io
        alert_data = parse_alert(message_text)
        send_to_smartbet(alert_data["event"], alert_data["bet"], alert_data["odds"])

        bot.send_message(chat_id=update.message.chat_id, text=f"✅ Sent to SmartBet: {alert_data['bet']} @ {alert_data['odds']}")
    return "OK", 200

# === FLASK ROOT ===
@app.route("/", methods=["GET"])
def index():
    return "🤖 Telegram SmartBet bot is running!", 200

# === SETUP WEBHOOK ===
if __name__ == "__main__":
    import asyncio

    async def setup_webhook():
        await bot.delete_webhook()
        await bot.set_webhook(url=WEBHOOK_URL)
        print(f"🌐 Webhook set to {WEBHOOK_URL}")

    asyncio.run(setup_webhook())
    print("🤖 Telegram bot running with webhook...")
    app.run(host="0.0.0.0", port=10000)
