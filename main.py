from flask import Flask, request
import requests
import logging
import os
import re

app = Flask(__name__)

# Telegram bot token and IFTTT webhook
BOT_TOKEN = os.environ.get("BOT_TOKEN")
IFTTT_URL = os.environ.get("IFTTT_URL")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

logging.basicConfig(level=logging.INFO)

def extract_event_and_bet(text):
    """
    Extract event name and bet from your Telegram alert.
    Event is before the color pattern line (🟥🟩🟥🟩🟩 - 🟩🟨🟩🟥🟩)
    Bet is on the first line after 'Bet :'
    """
    lines = text.splitlines()
    bet_line = ""
    event_line = ""
    
    # Extract bet
    for line in lines:
        if line.lower().startswith("bet"):
            bet_line = line.split(":", 1)[1].strip()
            break

    # Extract event (line before the line that contains color patterns)
    color_pattern_regex = re.compile(r"[\U0001F7E5-\U0001F7EB\U0001F7E6\U0001F7E7\U0001F7E8\U0001F7E9\- ]+")
    for i, line in enumerate(lines):
        if " - " in line and any(c in line for c in "🟥🟩🟨"):
            if i >= 1:
                event_line = lines[i - 1].replace(" vs ", " - ").strip()
            break

    return event_line, bet_line

@app.route("/", methods=["GET"])
def index():
    return "🤖 Telegram IFTTT Bot is running!"

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def receive_update():
    data = request.get_json()
    logging.info(f"Received update: {data}")

    try:
        message = data.get("message", {})
        text = message.get("text", "")
        chat_id = message.get("chat", {}).get("id")

        if text:
            # Extract event and bet
            event, bet = extract_event_and_bet(text)
            if not event:
                event = "Unknown Event"
            if not bet:
                bet = "Unknown Bet"

            # Prepare email body for SmartBet.io
            email_body = (
                f"SPORT: Football\n"
                f"EVENT: {event}\n"
                f"BET: {bet}\n"
                f"ODDS: 1.03\n"
                f"STAKE: 5\n"
                f"BOOK: Pinnacle\n"
                f"SOURCE: Kakason08>TelegramAlerts"
            )

            # Send to IFTTT
            payload = {"value1": email_body}
            r = requests.post(IFTTT_URL, json=payload, timeout=5)
            logging.info(f"✅ Sent to IFTTT ({r.status_code})")

            # Optional: reply to Telegram user
            if chat_id:
                reply = {"chat_id": chat_id, "text": "✅ Message sent to IFTTT!"}
                requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=reply)
    except Exception as e:
        logging.error(f"Error: {e}")

    return "OK", 200

if __name__ == "__main__":
    # Set webhook
    webhook_url = f"https://telegram-ifttt-bot.onrender.com/{BOT_TOKEN}"
    r = requests.post(f"{TELEGRAM_API_URL}/setWebhook", data={"url": webhook_url})
    logging.info(f"🌐 Webhook set to {webhook_url}")
    app.run(host="0.0.0.0", port=10000)
