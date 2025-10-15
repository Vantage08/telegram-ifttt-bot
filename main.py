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

    try:
        # Extract message text safely
        message = data.get("message", {})
        text = message.get("text", "")
        chat_id = message.get("chat", {}).get("id")

        if text:
            lines = text.splitlines()
            bet_line = lines[0].strip() if lines else ""
            event_line = None

            # Find first meaningful line after Bet line for EVENT
            for line in lines[1:]:
                clean_line = line.strip()
                if clean_line and not clean_line.startswith(("🇦","🟥","🟩","🟨")):
                    event_line = clean_line
                    break

            BET = bet_line.split("Bet :")[-1].strip() if "Bet :" in bet_line else bet_line
            EVENT = event_line if event_line else "Unknown Event"

            # Build payload for IFTTT / Gmail
            payload = {
                "value1": f"SPORT: Football",
                "value2": f"EVENT: {EVENT}",
                "value3": f"BET: {BET} ODDS: 1.03 STAKE: 5 BOOK: Pinnacle SOURCE: Kakason08>TelegramAlerts"
            }

            # Send to IFTTT
            r = requests.post(IFTTT_URL, json=payload, timeout=3)
            logging.info(f"✅ Sent to IFTTT ({r.status_code})")

            # Optional: reply to user in Telegram
            reply = {"chat_id": chat_id, "text": "✅ Message sent to SmartBet.io!"}
            requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=reply)

    except Exception as e:
        logging.error(f"Error: {e}")

    return "OK", 200  # respond fast

if __name__ == "__main__":
    # Set webhook
    webhook_url = f"https://telegram-ifttt-bot.onrender.com/{BOT_TOKEN}"
    r = requests.post(f"{TELEGRAM_API_URL}/setWebhook", data={"url": webhook_url})
    logging.info(f"🌐 Webhook set to {webhook_url}")

    # Run Flask app
    app.run(host="0.0.0.0", port=10000)
