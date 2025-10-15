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
        # Extract message text safely
        message = data.get("message", {})
        text = message.get("text", "")
        chat_id = message.get("chat", {}).get("id")

        if text:
            # --- Extract EVENT and BET from alert ---
            # Event line is before the color line (🟥🟩🟨...)
            event_block_match = re.search(r"\n(.+?)\n[🟥🟩🟨\-]+", text, re.DOTALL)
            event_block = event_block_match.group(1).strip() if event_block_match else "Unknown"

            event_lines = event_block.split("\n")
            if len(event_lines) >= 2:
                event_str = event_lines[1].replace("vs", "-").strip()  # Match only
            else:
                event_str = event_lines[0].replace("vs", "-").strip()

            # BET is on the first line after "Bet :"
            bet_match = re.search(r"Bet\s*:\s*(.+)", text)
            bet_str = bet_match.group(1).strip() if bet_match else "Unknown"

            # --- Prepare payload for IFTTT ---
            payload = {
                "value1": event_str,  # EVENT
                "value2": bet_str,    # BET
                "value3": "Football"  # SPORT (constant)
            }

            # Send to IFTTT
            requests.post(IFTTT_URL, json=payload, timeout=3)
            logging.info("✅ Sent to IFTTT")

            # Optional: reply to user in Telegram
            reply = {"chat_id": chat_id, "text": "✅ Message sent to IFTTT!"}
            requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=reply)
    except Exception as e:
        logging.error(f"Error: {e}")

    return "OK", 200  # respond fast

if __name__ == "__main__":
    # Set webhook
    webhook_url = f"https://telegram-ifttt-bot.onrender.com/{BOT_TOKEN}"
    r = requests.post(f"{TELEGRAM_API_URL}/setWebhook", data={"url": webhook_url})
    logging.info(f"🌐 Webhook set to {webhook_url}")

    app.run(host="0.0.0.0", port=10000)
