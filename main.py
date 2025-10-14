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
SOURCE = "Vantage08>TelegramAlerts"
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

    # Bet type
    for line in lines:
        if line.lower().startswith("bet :"):
            bet = line.split(":")[1].strip().upper()
            break

    # Event (detect " vs " line)
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
        "odds": "0.0",  # Let SmartBet.io use live Pinnacle odds
        "stake": STAKE,
        "book": BOOK,
        "source": SOURCE
    }

    try:
        # ✅ Use form data instead of JSON
        response = requests.post(SMARTBET_URL, data=payload, timeout=15)

        print(f"✅ Sent to SmartBet.io: {response.url if hasattr(response, 'url') else SMARTBET_URL}")
        print(f"🔄 Response Text: {response.text}")

        # Attempt to parse SmartBet.io's response
        pickid = "N/A"
        try:
            if response.headers.get("Content-Type", "").startswith("application/json"):
                resp_json = response.json()
                pickid = resp_json.get("pickid", "N/A")
            elif "pickid" in response.text.lower():
                # Try to extract pickid manually if it's text-based
                pickid = response.text.split("pickid")[-1].split()[0]
        except Exception as e:
            print(f"⚠️ Could not parse SmartBet.io response: {e}")

        # Log to file
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps({
                "event": event,
                "bet": bet,
                "response": response.text,
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

    if "Bet :" in text:
        alert_data = parse_alert(text)
        pickid = send_to_smartbet(alert_data["event"], alert_data["bet"])
        if pickid and pickid != "N/A":
            await update.message.reply_text(f"✅ Pick sent to SmartBet.io! Pick ID: {pickid}")
        else:
            await update.message.reply_text("⚠️ Pick sent but no Pick ID received — check SmartBet.io dashboard.")

# === START FLASK + TELEGRAM BOT ===
if __name__ == '__main__':
    # Run Flask in background thread
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))).start()

    # Start Telegram bot
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Telegram bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
