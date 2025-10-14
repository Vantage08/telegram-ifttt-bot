import os
import json
import smtplib
from email.message import EmailMessage
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, ContextTypes, MessageHandler, filters

# === CONFIGURATION ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
SMARTBET_EMAIL = "picks@smartbet.io"
SOURCE = os.getenv("SOURCE", "Kakason08")
STAKE = 5
BOOK = "Pinnacle"
ODDS = 1.0  # SmartBet.io will place at Pinnacle live odds

# === FLASK APP FOR WEBHOOK ===
app = Flask(__name__)
bot = Bot(BOT_TOKEN)

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def telegram_webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, bot)
    # Process in background
    from threading import Thread
    Thread(target=lambda: app.loop.create_task(handle_message(update))).start()
    return "OK", 200

# === PARSE TELEGRAM ALERT ===
def parse_alert(message_text):
    lines = message_text.split("\n")
    event = None
    bet = None

    for line in lines:
        if line.lower().startswith("bet :"):
            bet = line.split(":", 1)[1].strip().upper()
        if " vs " in line.lower():
            event = line.strip().replace(" vs ", " - ").replace(" VS ", " - ")

    return {"event": event or "Unknown Event", "bet": bet or "UNKNOWN"}

# === SEND EMAIL TO SMARTBET.IO ===
def send_email(event, bet):
    try:
        msg = EmailMessage()
        msg['From'] = GMAIL_ADDRESS
        msg['To'] = SMARTBET_EMAIL
        msg['Subject'] = f"New Pick: {event}"
        body = f"""SPORT: Football
EVENT: {event}
BET: {bet}
ODDS: {ODDS}
STAKE: {STAKE}
BOOK: {BOOK}
SOURCE: {SOURCE}
"""
        msg.set_content(body)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            smtp.send_message(msg)
        print(f"✅ Email sent to SmartBet.io:\n{body}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

# === TELEGRAM MESSAGE HANDLER ===
async def handle_message(update: Update):
    if not update.message or not update.message.text:
        return

    text = update.message.text
    if "Bet :" in text:
        alert_data = parse_alert(text)
        success = send_email(alert_data["event"], alert_data["bet"])
        reply_text = "✅ Pick sent to SmartBet.io!" if success else "❌ Failed to send pick."
        await update.message.reply_text(reply_text)

# === SET TELEGRAM WEBHOOK ===
async def setup_webhook():
    await bot.delete_webhook()
    await bot.set_webhook(url=f"https://telegram-ifttt-bot.onrender.com/{BOT_TOKEN}")
    print("🤖 Webhook set successfully!")

# === START FLASK APP ===
if __name__ == "__main__":
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(setup_webhook())
    print("🌐 Flask server running...")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
