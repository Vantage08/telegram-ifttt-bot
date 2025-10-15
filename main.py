import os
import smtplib
from email.message import EmailMessage
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import asyncio

# === CONFIGURATION ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g. https://yourapp.onrender.com/<BOT_TOKEN>
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
SMARTBET_EMAIL = "picks@smartbet.io"
SOURCE = os.getenv("SOURCE", "Kakason08")  # Your SmartBet.io source
STAKE = 5
BOOK = "PINNACLE"
ODDS = 1.0  # let SmartBet.io use live Pinnacle odds

# === FLASK HEALTH CHECK ===
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running", 200

# === HELPER: SEND PICK VIA EMAIL TO SMARTBET.IO ===
def send_pick_email(sport, event, bet):
    msg = EmailMessage()
    msg['Subject'] = f"New pick: {event}"
    msg['From'] = GMAIL_ADDRESS
    msg['To'] = SMARTBET_EMAIL

    msg.set_content(
        f"SPORT: {sport}\n"
        f"EVENT: {event}\n"
        f"BET: {bet}\n"
        f"ODDS: {ODDS}\n"
        f"STAKE: {STAKE}\n"
        f"BOOK: {BOOK}\n"
        f"SOURCE: user>{SOURCE}"
    )

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            smtp.send_message(msg)
        print(f"✅ Pick email sent: {event} | {bet}")
        return True
    except Exception as e:
        print(f"❌ Failed to send pick email: {e}")
        return False

# === HELPER: PARSE TELEGRAM ALERT ===
def parse_alert(text):
    lines = text.split("\n")
    event = None
    bet = None

    # Extract bet
    for line in lines:
        if line.lower().startswith("bet :"):
            bet = line.split(":")[1].strip()
            break

    # Extract event (look for " vs ")
    for line in lines:
        if " vs " in line.lower():
            event = line.strip().replace(" vs ", " - ").replace(" VS ", " - ")
            break

    return {"event": event or "Unknown Event", "bet": bet or "UNKNOWN"}

# === TELEGRAM HANDLER ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text:
        return

    # Only process messages containing a bet
    if "Bet :" in text:
        alert_data = parse_alert(text)
        success = send_pick_email("Football", alert_data["event"], alert_data["bet"])
        if success:
            await update.message.reply_text(f"✅ Pick sent to SmartBet.io: {alert_data['event']} | {alert_data['bet']}")
        else:
            await update.message.reply_text("❌ Failed to send pick to SmartBet.io.")

# === SETUP TELEGRAM WEBHOOK ===
async def setup_webhook():
    bot = Bot(token=BOT_TOKEN)
    await bot.delete_webhook()
    await bot.set_webhook(url=WEBHOOK_URL)
    print("🤖 Webhook set successfully!")

# === START APP ===
if __name__ == '__main__':
    # Run async webhook setup
    asyncio.run(setup_webhook())

    # Telegram bot
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🌐 Telegram bot is running...")

    # Run Flask app (health check + webhook receiver)
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
