import os
import smtplib
from email.mime.text import MIMEText
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import asyncio

# Environment variables
TOKEN = os.environ.get("TELEGRAM_TOKEN")  # Telegram Bot token from BotFather
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # e.g., https://yourdomain.com/<TOKEN>
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")  # Your Gmail address
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")  # Gmail app password
SMARTBET_EMAIL = "picks@smartbet.io"  # Smartbet.io picks email
SMARTBET_SOURCE = "Kakason08"  # Your Smartbet.io source

# Initialize bot
bot = Bot(token=TOKEN)
application = ApplicationBuilder().token(TOKEN).build()

# Flask app
app = Flask(__name__)

# Helper function to send pick email
def send_pick_email(sport, event, bet, odds=1.0, stake=5, book="Pinnacle"):
    """
    Sends a pick email to Smartbet.io.
    odds=1.0 will use Pinnacle live odds.
    stake is fixed at 5.
    """
    body = f"""SPORT: {sport}
EVENT: {event}
BET: {bet}
ODDS: {odds}
STAKE: {stake}
BOOK: {book}
SOURCE: {SMARTBET_SOURCE}"""
    
    msg = MIMEText(body)
    msg["Subject"] = f"Pick: {event}"
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = SMARTBET_EMAIL

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, SMARTBET_EMAIL, msg.as_string())
        print(f"✅ Pick sent: {event}")
    except Exception as e:
        print(f"❌ Error sending pick: {e}")

# Telegram message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    # Example: simple parsing assuming format "Over 0.5 Victoria Hamburg - Osdorf"
    if text:
        try:
            parts = text.split(" ", 1)
            bet = parts[0]  # e.g., "Over 0.5"
            event = parts[1]  # e.g., "Victoria Hamburg - Osdorf"
            send_pick_email(sport="Football", event=event, bet=bet)
        except Exception as e:
            print(f"❌ Error processing message: {e}")

# Add handler
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Synchronous webhook for Flask
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    """Receive Telegram updates synchronously"""
    try:
        update = Update.de_json(request.get_json(force=True), bot)
        asyncio.run(application.process_update(update))
    except Exception as e:
        print(f"❌ Error handling update: {e}")
    return "ok", 200

# Start Flask
if __name__ == "__main__":
    # Set webhook
    asyncio.run(bot.set_webhook(url=WEBHOOK_URL))
    print(f"🤖 Webhook set to {WEBHOOK_URL}")
    print("🌐 Telegram bot is running on Render...")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
