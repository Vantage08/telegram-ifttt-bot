from flask import Flask, request
import requests
import logging
import os

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

    # Acknowledge Telegram immediately
    try:
        # Extract message text safely
        message = data.get("message", {})
        text = message.get("text", "")
        chat_id = message.get("chat", {}).get("id")

        if text:
            # Forward message to IFTTT
            payload = {
                "value1": text,
                "value2": message.get("from", {}).get("first_name", ""),
                "value3": message.get("date", "")
            }
            requests.post(IFTTT_URL, json=payload, timeout=3)
            logging.info("✅ Sent to IFTTT")

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
