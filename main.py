from flask import Flask, request
import requests
import logging
import os

app = Flask(__name__)

# Telegram bot token and IFTTT webhook URL from environment variables
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
            # Split message into lines
            lines = text.splitlines()

            # Extract BET (first line starting with "Bet :")
            bet_line = next((l for l in lines if l.startswith("Bet :")), "")
            BET = bet_line.replace("Bet :", "").strip() if bet_line else text.strip()

            # Extract EVENT (line before the first line that contains any colored squares)
            EVENT = "Unknown Event"
            for i, line in enumerate(lines):
                if any(c in line for c in "🟥🟩🟨"):
                    if i > 0:
                        EVENT = lines[i - 1].strip().replace(" vs ", " - ")
                    break

            # Prepare payload for IFTTT
            payload = {
                "value1": "Football",  # SPORT
                "value2": EVENT,       # EVENT
                "value3": f"BET: {BET} ODDS: 1.03 STAKE: 5 BOOK: Pinnacle SOURCE: Kakason08>TelegramAlerts"
            }

            # Send to IFTTT
            r = requests.post(IFTTT_URL, json=payload, timeout=5)
            if r.status_code == 200:
                logging.info("✅ Sent to IFTTT")
                reply_text = "✅ Sent to SmartBet.io (Stake: 5, Odds: 1.03)"
            else:
                logging.error(f"❌ IFTTT error: {r.status_code} {r.text}")
                reply_text = "❌ Failed to send to SmartBet.io"

            # Optional: reply to Telegram
            reply = {"chat_id": chat_id, "text": reply_text}
            requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=reply, timeout=5)

    except Exception as e:
        logging.error(f"Error: {e}")

    return "OK", 200

if __name__ == "__main__":
    # Set webhook
    webhook_url = f"https://telegram-ifttt-bot.onrender.com/{BOT_TOKEN}"
    r = requests.post(f"{TELEGRAM_API_URL}/setWebhook", data={"url": webhook_url})
    logging.info(f"🌐 Webhook set to {webhook_url}")

    # Run Flask server
    app.run(host="0.0.0.0", port=10000)
