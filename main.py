import os
import smtplib
from email.message import EmailMessage
from flask import Flask, request
from telegram import Update, Bot

# === CONFIGURATION ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # https://yourapp.onrender.com/<BOT_TOKEN>
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
SMARTBET_EMAIL = "picks@smartbet.io"

STAKE = 5
BOOK = "Pinnacle"
ODDS = 1.0
SOURCE = os.getenv("SMARTBET_SOURCE", "Kakason08")

# === FLASK APP ===
app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)

# === HELPER: Parse Telegram Alert ===
def parse_alert(text: str):
    lines = text.split("\n")
    bet = None
    event = None

    for line in lines:
        if line.lower().startswith("bet :"):
            bet = line.split(":", 1)[1].strip()
        if " vs " in line.lower():
            event = line.strip()
    return bet, event

# === HELPER: Send email to SmartBet.io ===
def send_email_to_smartbet(bet, event):
    msg = EmailMessage()
    msg["Subject"] = f"Pick: {bet} | {event}"
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = SMARTBET_EMAIL

    body = f"""SPORT: Football
EVENT: {event}
BET: {bet}
ODDS: {ODDS}
STAKE: {STAKE}
BOOK: {BOOK}
SOURCE: {SOURCE}
"""
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            smtp.send_message(msg)
        print(f"✅ Pick sent via email to SmartBet.io:\n{body}")
    except Exception as e:
        print(f"❌ Failed to send pick: {e}")

# === FLASK ROUTE TO HANDLE TELEGRAM UPDATES ===
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    if update.message and update.message.text:
        text = update.message.text
        if "Bet :" in text:
            bet, event = parse_alert(text)
            if bet and event:
                send_email_to_smartbet(bet, event)
                bot.send_message(chat_id=update.message.chat_id, 
                                 text=f"✅ Pick sent to SmartBet.io!\nEvent: {event}\nBet: {bet}")
    return "OK", 200

# === ROOT ROUTE FOR HEALTHCHECK ===
@app.route("/")
def index():
    return "Bot is running", 200

# === SET TELEGRAM WEBHOOK ===
def set_webhook():
    bot.delete_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    print("🤖 Webhook set successfully!")

if __name__ == "__main__":
    set_webhook()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
