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
SOURCE = os.getenv("SOURCE", "TelegramAlerts")
LOG_FILE = os.getenv("LOG_FILE", "smartbet_picks.log")

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

    # Find Bet
    for line in lines:
        if line.lower().startswith("bet :"):
            bet = line.split(":")[1].strip().upper()
            break

    # Find Event
    for line in lines:
        if " vs " in line.lower():
            event = line.strip().replace(" vs ", " - ").replace(" VS ", " - ")
            break

    return {"event": event or "Unknown Event", "bet": bet or "UNKNOWN"}


# === SEND PICK TO SMARTBET.IO (GET METHOD) ===
def send_to_smartbet(event, bet):
    params = {
        "key": SMARTBET_KEY,
        "sport": SPORT,
        "event": event,
        "bet": bet,
        "odds": "0.0",   # SmartBet will use Pinnacle's live odds
        "stake": STAKE,
        "book": BOOK,
        "source": SOURCE
    }
    try:
        response = requests.get(SMARTBET_URL, params=params)
        print(f"✅ Sent to SmartBet.io: {response.url}")
        print(f"🔄 Response: {response.text}")

        # Try to parse JSON if SmartBet returns one
        try:
            resp_json = response.json()
            pickid = resp_json.get("pickid", "N/A")
        except:
            pickid = "N/A"

        # Log pick
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


# === TELEGRAM HANDLER ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text:
        return

    # Process messages that contain 'Bet :'
    if "Bet :" in text:
        alert_data = parse_alert(text)
        pickid = send_to_smartbet(alert_data["event"], alert_data["bet"])
        if pickid and pickid != "N/A":
            await update.message.reply_text(f"✅ Pick sent to SmartBet.io! Pick ID: {pickid}")
        else:
            await update.message.reply_text("✅ Pick sent to SmartBet.io! (no Pick ID returned)")

# === START FLASK + TELEGRAM BOT ===
if __name__ == '__main__':
    # Run Flask in a background thread
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))).start()

    # Run Telegram bot in main thread
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Telegram bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
