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

        if text:
            # --- Extract parameters from Telegram alert ---
            # Bet line (first line starting with "Bet :")
            bet_match = re.search(r"Bet\s*:\s*(.+)", text)
            bet_str = bet_match.group(1).strip() if bet_match else "Unknown"

            # Event line is always before the color line (🟥🟩...)
            event_match = re.search(r"\n(.+?)\n[🟥🟩🟨\-]+", text, re.DOTALL)
            event_str = event_match.group(1).strip() if event_match else "Unknown"
            # Replace "vs" with "-" in event
            event_str = event_str.replace("vs", "-").replace("\n", " ")

            # Build the email body
            email_body = (
                f"SPORT: Football\n"
                f"EVENT: {event_str}\n"
                f"BET: {bet_str}\n"
                f"ODDS: 1.03\n"
                f"STAKE: 5\n"
                f"BOOK: Pinnacle\n"
                f"SOURCE: Kakason08>TelegramAlerts"
            )

            # --- Send to IFTTT ---
            payload = {
                "value1": email_body,
                "value2": "",
                "value3": ""
            }
            r = requests.post(IFTTT_URL, json=payload, timeout=3)
            logging.info(f"✅ Sent to IFTTT ({r.status_code})")

            # Optional: reply to user
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
