from flask import Flask, request
import requests
import logging
import os
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

# --- Configuration ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
EMAIL_USER = os.environ.get("EMAIL_USER")      # your Gmail address
EMAIL_PASS = os.environ.get("EMAIL_PASS")      # your Gmail app password
TO_EMAIL = "picks@smartbet.io"

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

logging.basicConfig(level=logging.INFO)

@app.route("/", methods=["GET"])
def index():
    return "🤖 Telegram Email Bot is running!"

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def receive_update():
    data = request.get_json()
    logging.info(f"Received update: {data}")

    try:
        message = data.get("message", {})
        text = message.get("text", "")
        chat_id = message.get("chat", {}).get("id")

        if text:
            # --- Extract Bet and Event ---
            bet_match = re.search(r"Bet\s*:\s*(.+)", text)
            bet_str = bet_match.group(1).strip() if bet_match else "Unknown"

            # Event = line before color pattern
            event_match = re.search(r"\n(.+?)\n[🟥🟩🟨🟦🟧🟪⬜⬛\- ]+", text, re.DOTALL)
            event_str = event_match.group(1).strip() if event_match else "Unknown"
            event_str = event_str.replace("vs", "-")

            # --- Format email body ---
            email_body = f"""SPORT: Football
EVENT: {event_str}
BET: {bet_str}
ODDS: 1.03
STAKE: 5
BOOK: Pinnacle
SOURCE: Kakason08>TelegramAlerts"""

            # --- Send Email via Gmail SMTP ---
            msg = MIMEMultipart()
            msg["From"] = EMAIL_USER
            msg["To"] = TO_EMAIL
            msg["Subject"] = f"SmartBet Alert - {event_str}"

            msg.attach(MIMEText(email_body, "plain"))

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(EMAIL_USER, EMAIL_PASS)
                server.send_message(msg)

            logging.info("✅ Email sent successfully to SmartBet.io")

            # --- Reply to Telegram ---
            reply = {"chat_id": chat_id, "text": "✅ Email sent to SmartBet.io!"}
            requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=reply)

    except Exception as e:
        logging.error(f"Error: {e}")

    return "OK", 200


if __name__ == "__main__":
    webhook_url = f"https://telegram-ifttt-bot.onrender.com/{BOT_TOKEN}"
    r = requests.post(f"{TELEGRAM_API_URL}/setWebhook", data={"url": webhook_url})
    logging.info(f"🌐 Webhook set to {webhook_url}")
    app.run(host="0.0.0.0", port=10000)
