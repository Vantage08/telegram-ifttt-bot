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
    Extract the bet and event from the Telegram alert.
    Assumes:
    - First line starts with "Bet : ..."
    - Event name is the line **before** the color arrangement (🟥🟩...).
    """
    lines = text.splitlines()
    
    # Extract bet
    bet_line = next((l for l in lines if l.startswith("Bet :")), "")
    bet = bet_line.replace("Bet :", "").strip() if bet_line else ""
    
    # Find event line: the line before the one that contains color blocks
    event = ""
    for i, line in enumerate(lines):
        if re.search(r"[🟥🟩🟨🟦]", line):
            if i > 0:
                event = lines[i-1].strip()
                break
    
    # Replace "vs" with "-"
    event = event.replace(" vs ", " - ").replace("VS", "-").replace("Vs", "-")
    
    return event, bet

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
            event, bet = extract_event_and_bet(text)

            payload = {
                "value1": "Football",  # SPORT
                "value2": event,       # EVENT
                "value3": bet          # BET
            }

            # Send to IFTTT
            r = requests.post(IFTTT_URL, json=payload, timeout=5)
            logging.info(f"✅ Sent to IFTTT ({r.status_code})")

            # Reply to user in Telegram
            reply = {"chat_id": chat_id, "text": f"✅ Sent to SmartBet.io!\nEvent: {event}\nBet: {bet}"}
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
