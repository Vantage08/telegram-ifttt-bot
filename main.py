from flask import Flask, request
import requests
import logging

app = Flask(__name__)

# --- Configuration ---
BOT_TOKEN = "8201436530:AAHEpYYe-85_AShCBszmnCalk2I9v3YZoIg"
IFTTT_URL = "https://maker.ifttt.com/trigger/telegram_alert/with/key/c6QsqQqCIl9LzH6X2Oo04yAbYvsAfrCLP44qy9_sCt2"

logging.basicConfig(level=logging.INFO)

@app.route('/')
def home():
    return "Bot is running!"

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def telegram_webhook():
    update = request.get_json()
    logging.info(update)

    if "message" in update and "text" in update["message"]:
        text = update["message"]["text"]
        chat_id = update["message"]["chat"]["id"]

        # Default placeholders
        bet = ""
        event = ""

        # Split into lines
        lines = text.splitlines()
        for line in lines:
            line = line.strip()

            # Extract Bet
            if line.lower().startswith("bet"):
                bet = line.split(":")[-1].strip()

            # Extract Event (contains 'vs')
            elif " vs " in line.lower():
                event = line.strip()

        if event and bet:
            # Send to IFTTT
            data = {
                "value1": event,
                "value2": bet
            }
            requests.post(IFTTT_URL, json=data)

            # Confirm to user
            msg = (
                f"✅ Sent to SmartBet.io\n"
                f"🏟️ Event: {event}\n"
                f"🎯 Bet: {bet}\n"
                f"💰 Stake: 5 | Odds: 1.03"
            )
            send_message(chat_id, msg)
        else:
            send_message(chat_id, "⚠️ Could not find 'Bet' or 'Event' in your message.")

    return "ok"

def send_message(chat_id, text):
    """Send Telegram message"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

if __name__ == '__main__':
    WEBHOOK_URL = f"https://telegram-ifttt-bot.onrender.com/{BOT_TOKEN}"
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
        json={"url": WEBHOOK_URL}
    )
    logging.info(f"🌐 Webhook set to {WEBHOOK_URL}")
    app.run(host="0.0.0.0", port=10000)
