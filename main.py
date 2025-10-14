import os
import json
import threading
import time
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, filters, ContextTypes, Dispatcher
import requests
import asyncio

# === CONFIGURATION ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
SMARTBET_KEY = os.getenv("SMARTBET_KEY")
SPORT = os.getenv("SPORT", "SOCCER")
STAKE = os.getenv("STAKE", "5")
BOOK = os.getenv("BOOK", "PINNACLE")
SOURCE = os.getenv("SOURCE", "Telegram>Alerts")
LOG_FILE = os.getenv("LOG_FILE", "smartbet_picks.log")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))  # seconds
PORT = int(os.environ.get("PORT", 10000))
WEBHOOK_PATH = "/telegram_webhook"
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # e.g., https://your-app.onrender.com/telegram_webhook

SMARTBET_POST_URL = "https://smartbet.io/postpick.php"
SMARTBET_STATUS_URL = "https://smartbet.io/pickstatus.php"

# === FLASK APP ===
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running", 200

@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, bot)
    asyncio.run(handle_update(update))
    return "ok", 200

# === TELEGRAM BOT ===
bot = Bot(token=BOT_TOKEN)
application = Application.builder().token(BOT_TOKEN).build()

# === PARSE TELEGRAM ALERT ===
def parse_alert(message_text):
    lines = message_text.split("\n")
    event = None
    bet = None
    for line in lines:
        if line.lower().startswith("bet :"):
            bet = line.split(":")[1].strip().upper()
            break
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
        "odds": "0.0",
        "stake": STAKE,
        "book": BOOK,
        "source": SOURCE
    }
    try:
        response = requests.post(SMARTBET_POST_URL, json=payload)
        resp_json = response.json()
        pickid = resp_json.get("pickid", None)

        print(f"✅ Sent to SmartBet.io: {json.dumps(payload)}")
        print(f"🔄 Response: {response.text}")
        print(f"🆔 Pick ID: {pickid}")

        if pickid:
            with open(LOG_FILE, "a") as f:
                f.write(json.dumps({
                    "event": event,
                    "bet": bet,
                    "pickid": pickid
                }) + "\n")
        return pickid
    except Exception as e:
        print(f"❌ Error sending to SmartBet.io: {e}")
        return None

# === CHECK PICK STATUS ===
def check_pick_status(pickid, chat_id):
    try:
        response = requests.post(SMARTBET_STATUS_URL, json={
            "key": SMARTBET_KEY,
            "pickid": str(pickid)
        })
        resp_json = response.json()
        status = resp_json.get("processing_status", "UNKNOWN")
        short_desc = resp_json.get("processing_result_short", "")
        execution = resp_json.get("execution_result", "")

        print(f"🔎 Pick ID {pickid} status: {status} - {short_desc} - {execution}")

        if status != "PROCESSED":
            bot.send_message(
                chat_id=chat_id,
                text=f"⚠️ Pick ID {pickid} status: {status}\n{short_desc}\nExecution: {execution}"
            )
    except Exception as e:
        print(f"❌ Error checking pick status for {pickid}: {e}")

# === HANDLE TELEGRAM UPDATE ===
async def handle_update(update: Update):
    if not update.message or not update.message.text:
        return

    text = update.message.text
    chat_id = update.message.chat_id

    if "Bet :" in text:
        alert_data = parse_alert(text)
        pickid = send_to_smartbet(alert_data["event"], alert_data["bet"])
        if pickid:
            await bot.send_message(chat_id, f"✅ Pick sent to SmartBet.io! Pick ID: {pickid}")
            # Start background status monitoring
            threading.Thread(target=status_monitor, args=(pickid, chat_id)).start()
        else:
            await bot.send_message(chat_id, "❌ Failed to send pick to SmartBet.io.")

# === STATUS MONITOR THREAD ===
def status_monitor(pickid, chat_id):
    for _ in range(5):  # check 5 times
        check_pick_status(pickid, chat_id)
        time.sleep(CHECK_INTERVAL)

# === SET TELEGRAM WEBHOOK ===
bot.delete_webhook()
bot.set_webhook(url=WEBHOOK_URL)

# === START FLASK APP ===
if __name__ == "__main__":
    print("🤖 Telegram bot running with webhook...")
    app.run(host="0.0.0.0", port=PORT)
