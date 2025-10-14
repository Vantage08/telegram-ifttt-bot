import os
import requests
from flask import Flask, request
from telegram import Update, Bot
import asyncio

# === CONFIGURATION ===
TOKEN = os.getenv("BOT_TOKEN")  # Telegram bot token
SMARTBET_KEY = os.getenv("SMARTBET_KEY")  # SmartBet API key
SPORT = "SOCCER"
STAKE = "5"
BOOK = "PINNACLE"
SOURCE = "Vantage08>TelegramAlerts"
SMARTBET_URL = "https://smartbet.io/postpick.php"

app = Flask(__name__)
bot = Bot(token=TOKEN)

@app.route("/")
def home():
    return "✅ Bot is running!", 200


@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    message = update.message.text if update.message else ""

    if not message:
        return "ok"

    bet = None
    event = None
    for line in message.split("\n"):
        if line.lower().startswith("bet :"):
            bet = line.split(":")[1].strip().upper()
        if " vs " in line.lower():
            event = line.strip().replace(" vs ", " - ").replace(" VS ", " - ")

    if bet and event:
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
            r = requests.post(SMARTBET_URL, data=payload)
            if r.status_code == 200:
                bot.send_message(chat_id=update.message.chat_id,
                                 text=f"✅ Pick sent to SmartBet.io! ({event} | {bet})")
                print(f"✅ SmartBet.io Response: {r.text}")
            else:
                bot.send_message(chat_id=update.message.chat_id,
                                 text=f"❌ SmartBet.io error: {r.status_code}")
                print(f"❌ SmartBet.io Error: {r.text}")
        except Exception as e:
            bot.send_message(chat_id=update.message.chat_id, text=f"⚠️ Error: {e}")
            print(f"⚠️ Exception sending to SmartBet.io: {e}")

    return "ok"


if __name__ == "__main__":
    async def setup_webhook():
        await bot.delete_webhook()
        await bot.set_webhook(url=f"https://telegram-ifttt-bot.onrender.com/{TOKEN}")
        print("🤖 Webhook set successfully!")

    asyncio.run(setup_webhook())

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
