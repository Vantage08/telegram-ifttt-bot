from flask import Flask, request
import requests
import logging
import os
import re

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
IFTTT_URL = os.environ.get("IFTTT_URL")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

logging.basicConfig(level=logging.INFO)

def parse_telegram_message(text):
    """Extract Bet and Event info from Telegram message."""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    bet = "N/A"
    event = "N/A"

    # Extract BET line
    for line in lines:
        if line.lower().startswith("bet"):
            bet = line.split(":", 1)[-1].strip()
            break

    # Extract EVENT (usually next line containing 'vs' or '-')
    for line in lines:
        if "vs" in line.lower() or "-" in line:
            event = line.strip()
            break

    return bet, event


@app.route("/", methods=["GET"])
def index():
    return "🤖 Telegram SmartBet Bot is running!"


@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def receive_update():
    data = request.get_json()
    logging.info(f"Received update: {data}")

    try:
        message = data.get("message", {})
        text = message.get("text", "")
        chat_id = message.get("chat", {}).get("id")

        if not text:
            return "OK", 200

        bet, event = parse_telegram_message(text)

        formatted_message = (
            f"SPORT: Football\n"
            f"EVENT: {event}\n"
            f"BET: {bet}\n"
            f"ODDS: 1.03\n"
            f"STAKE: 5\n"
            f"BOOK: Pinnacle\n"
            f"SOURCE: Kakason08>TelegramAlerts"
        )

        payload = {"value1": formatted_message}
        res = requests.post(IFTTT_URL, json=payload, timeout=3)
        logging.info(f"✅ Sent to IFTTT ({res.status_code})")

        reply = {
            "chat_id": chat_id,
            "text": f"✅ Sent to SmartBet.io\n\nEvent: {event}\nBet: {bet}\nStake: 5 | Odds: 1.03"
        }
        requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=reply)

    except Exception as e:
        logging.error(f"Error: {e}")

    return "OK", 200


if __name__ == "__main__":
    webhook_url = f"https://telegram-ifttt-bot.onrender.com/{BOT_TOKEN}"
    r = requests.post(f"{TELEGRAM_API_URL}/setWebhook", data={"url": webhook_url})
    logging.info(f"🌐 Webhook set to {webhook_url}")
    app.run(host="0.0.0.0", port=10000)
