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

        if not text:
            return "No text", 200

        # --- Extract EVENT ---
        # Event line is always the one before the color emoji line
        # The color line usually contains 🟥🟩🟨🟦 etc.
        event_match = re.search(r"([^\n]+)\n[🟥🟩🟨🟦🟧🟪🟫⬜⬛\- ]+", text)
        event_str = event_match.group(1).strip() if event_match else "Unknown Event"

        # Replace "vs" (in any case) with "-"
        event_str = re.sub(r"\bvs\b", "-", event_str, flags=re.IGNORECASE)

        # --- Extract BET ---
        bet_match = re.search(r"Bet\s*:\s*(.+)", text, re.IGNORECASE)
        bet_str = bet_match.group(1).strip() if bet_match else "Unknown Bet"

        # --- Prepare payload for IFTTT ---
        payload = {
            "value1": event_str,  # EVENT
            "value2": bet_str,    # BET
            "value3": "Football"  # SPORT (constant)
        }

        # --- Send to IFTTT ---
        try:
            res = requests.post(IFTTT_URL, json=payload, timeout=3)
            logging.info(f"✅ Sent to IFTTT: {payload}, response={res.status_code}")
        except Exception as err:
            logging.error(f"IFTTT error: {err}")

        # --- Reply to Telegram ---
        reply_text = f"✅ Sent to IFTTT!\nEvent: {event_str}\nBet: {bet_str}"
        requests.post(f"{TELEGRAM_API_URL}/sendMessage", json={"chat_id": chat_id, "text": reply_text})

    except Exception as e:
        logging.error(f"Error: {e}")

    return "OK", 200


if __name__ == "__main__":
    # Set webhook automatically
    webhook_url = f"https://telegram-ifttt-bot.onrender.com/{BOT_TOKEN}"
    r = requests.post(f"{TELEGRAM_API_URL}/setWebhook", data={"url": webhook_url})
    logging.info(f"🌐 Webhook set to {webhook_url}")

    app.run(host="0.0.0.0", port=10000)
