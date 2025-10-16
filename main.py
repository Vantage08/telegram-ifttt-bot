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
            return "OK", 200

        # --- Extract Event and Bet ---
        bet_match = re.search(r"(?i)Bet\s*:\s*(.+)", text)
        bet = bet_match.group(1).strip() if bet_match else "N/A"

        # The event is always before the colored form sequence (🟥🟩... etc)
        event_match = re.search(r"\n([^\n]+?)\s*\n.*?🟥|🟩|🟨", text)
        if event_match:
            event = event_match.group(1).strip()
        else:
            # Fallback: try line after league name
            lines = text.split("\n")
            event = next((l.strip() for l in lines if "vs" in l or "-" in l), "N/A")

        # Replace "vs" with "-"
        event = event.replace("vs", "-")

        # --- Clean formatted body for email ---
        email_body = (
            f"SPORT: Football\n"
            f"EVENT: {event}\n"
            f"BET: {bet}\n"
            f"ODDS: 1.03\n"
            f"STAKE: 5\n"
            f"BOOK: Pinnacle\n"
            f"SOURCE: Kakason08>TelegramAlerts"
        )

        # --- Send to IFTTT ---
        payload = {"value1": email_body}
        res = requests.post(IFTTT_URL, json=payload, timeout=3)
        logging.info(f"✅ Sent to IFTTT ({res.status_code})")

        # --- Optional Telegram confirmation ---
        if chat_id:
            reply = {"chat_id": chat_id, "text": "✅ Sent to SmartBet.io (Stake: 5, Odds: 1.03)"}
            requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=reply)

    except Exception as e:
        logging.error(f"Error: {e}")

    return "OK", 200


if __name__ == "__main__":
    webhook_url = f"https://telegram-ifttt-bot.onrender.com/{BOT_TOKEN}"
    r = requests.post(f"{TELEGRAM_API_URL}/setWebhook", data={"url": webhook_url})
    logging.info(f"🌐 Webhook set to {webhook_url}")
    app.run(host="0.0.0.0", port=10000)
