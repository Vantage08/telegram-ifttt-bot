import os
import json
import threading
import time
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
LOG_FILE = os.getenv("LOG_FILE", "smartbet_picks.log")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))  # seconds

SMARTBET_POST_URL = "https://smartbet.io/postpick.php"
SMARTBET_STATUS_URL = "https://smartbet.io/pickstatus.php"

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

    for line in lines:
        if line.lower().startswith("bet :"):
            bet = line.split(":")[1].strip().upper()
            break

    for line in lines:
        if " vs " in line.lower():
            event = line.strip().replace(" vs ", " - ").replace(" VS ", " - ")
            break

    return {"event": event or "Unknown Event", "bet": bet or "UNKNOWN"}

# === SEND PICK TO SMARTBET.IO AND LOG PICK ID ===
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
def check_pick_status(bot, pickid):
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

        # Notify Telegram if pick failed
        if status != "PROCESSED":
            bot.loop.create_task(
                bot.bot.send_message(
                    chat_id=bot.chat_id,
                    text=f"⚠️ Pick ID {pickid} status: {status}\n{short_desc}\nExecution: {execution}"
                )
            )
    except Exception as e:
        print(f"❌ Error checking pick status for {pickid}: {e}")

# === TELEGRAM HANDLER ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text:
        return

    if "Bet :" in text:
        alert_data = parse_alert(text)
        pickid = send_to_smartbet(alert_data["event"], alert_data["bet"])
        if pickid:
            await update.message.reply_text(f"✅ Pick sent to SmartBet.io! Pick ID: {pickid}")
            # Save chat_id for notifications
            context.chat_data['chat_id'] = update.message.chat_id
            # Start a background thread to check status
            threading.Thread(target=status_monitor, args=(context, pickid)).start()
        else:
            await update.message.reply_text("❌ Failed to send pick to SmartBet.io.")

# === BACKGROUND STATUS MONITOR ===
def status_monitor(context, pickid):
    chat_id = context.chat_data.get('chat_id')
    if not chat_id:
        return
    class DummyBot:
        bot = context.application
        chat_id = chat_id

    # Check pick status every CHECK_INTERVAL seconds, 5 times
    for _ in range(5):
        check_pick_status(DummyBot, pickid)
        time.sleep(CHECK_INTERVAL)

# === START FLASK + TELEGRAM BOT ===
if __name__ == '__main__':
    # Run Flask in a background thread
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))).start()

    # Run Telegram bot in main thread
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Telegram bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
