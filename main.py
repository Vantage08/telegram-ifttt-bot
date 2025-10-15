from flask import Flask, request
import os
import smtplib
from email.mime.text import MIMEText
from telegram import Bot, Update

# Environment variables
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", f"https://telegram-ifttt-bot.onrender.com/{TOKEN}")
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

bot = Bot(token=TOKEN)
app = Flask(__name__)

# ========== SMARTBET.IO EMAIL FUNCTION ==========
def send_to_smartbet(sport, event, bet, odds, stake, book, source):
    body = f"""SPORT: {sport}
EVENT: {event}
BET: {bet}
ODDS: {odds}
STAKE: {stake}
BOOK: {book}
SOURCE: {source}"""
    msg = MIMEText(body)
    msg["Subject"] = "New SmartBet Pick"
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = "picks@smartbet.io"

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        print("✅ Email sent to SmartBet.io successfully.")
    except Exception as e:
        print(f"❌ Email sending failed: {e}")

# ========== TELEGRAM WEBHOOK HANDLER ==========
@app.route(f"/{TOKEN}", methods=["POST"])
def receive_update():
    try:
        update = Update.de_json(request.get_json(force=True), bot)
        message = update.message.text if update.message else None

        if message:
            # Example alert message: "Football - Victoria Hamburg - Osdorf - Over 0.5"
            parts = message.split(" - ")
            if len(parts) >= 4:
                sport = parts[0]
                event = parts[1] + " - " + parts[2]
                bet = parts[3]
                odds = "1.0"
                stake = "5"
                book = "PINNACLE"
                source = "Kakason08"

                send_to_smartbet(sport, event, bet, odds, stake, book, source)
                bot.send_message(chat_id=update.message.chat_id, text="✅ Pick sent to SmartBet.io successfully!")
            else:
                bot.send_message(chat_id=update.message.chat_id, text="⚠️ Invalid pick format.")
        return "ok", 200

    except Exception as e:
        print(f"❌ Error: {e}")
        return "error", 500


# ========== MAIN ==========
if __name__ == "__main__":
    try:
        bot.delete_webhook()
        bot.set_webhook(url=WEBHOOK_URL)
        print(f"🤖 Webhook set to {WEBHOOK_URL}")
    except Exception as e:
        print(f"⚠️ Webhook setup failed: {e}")

    print("🌐 Telegram bot is running...")
    app.run(host="0.0.0.0", port=10000)
