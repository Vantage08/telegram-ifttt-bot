import os
import requests
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# --- Load environment variables ---
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SMARTBET_KEY = os.getenv("SMARTBET_KEY")
SPORT = os.getenv("SPORT", "SOCCER")
BET_TYPE = os.getenv("BET_TYPE", "UNDER 0.5")
BOOK = os.getenv("BOOK", "PINNACLE")
STAKE = os.getenv("STAKE", "5")
SOURCE = "smb.Vantage08>TelegramAlerts"

# --- Flask app for Render pinging ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Telegram → SmartBet bot is running successfully!"

# --- Telegram message handler ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    message = update.message.text.strip()

    # Skip messages from the bot itself
    if update.message.from_user.is_bot:
        return

    print(f"Received Telegram message: {message}")

    # Format the event from the alert message
    event = message.replace("\n", " ").strip()

    # Send to SmartBet.io via POST
    payload = {
        "key": SMARTBET_KEY,
        "sport": SPORT,
        "event": event,
        "bet": BET_TYPE,
        "stake": STAKE,
        "book": BOOK,
        "source": SOURCE
    }

    try:
        response = requests.post("https://smartbet.io/postpick.php", json=payload)
        print(f"Sent to SmartBet.io | Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print(f"Error sending to SmartBet.io: {e}")

# --- Start Telegram bot ---
def run_telegram_bot():
    print("Starting Telegram bot...")
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app_bot.run_polling()

if __name__ == '__main__':
    import threading
    threading.Thread(target=run_telegram_bot).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
