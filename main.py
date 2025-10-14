import os
import smtplib
from email.mime.text import MIMEText
import threading
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# === CONFIGURATION ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")           # Your Gmail address (environment variable)
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD") # Your Gmail App Password (environment variable)
SMARTBET_EMAIL = "picks@smartbet.io"
SOURCE = os.getenv("SOURCE", "Kakason08")           # SmartBet.io source
STAKE = "5"
BOOK = "Pinnacle"
SPORT_DEFAULT = "Football"

# === FLASK HEALTH CHECK ===
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running", 200

# === PARSE TELEGRAM ALERT ===
def parse_alert(message_text):
    lines = message_text.split("\n")
    event = None
    bet = None

    # Bet type
    for line in lines:
        if line.lower().startswith("bet :"):
            bet = line.split(":")[1].strip()
            break

    # Event
    for line in lines:
        if " vs " in line.lower():
            event = line.strip().replace(" vs ", " - ").replace(" VS ", " - ")
            break

    return {
        "sport": SPORT_DEFAULT,
        "event": event or "Unknown Event",
        "bet": bet or "UNKNOWN",
        "stake": STAKE,
        "book": BOOK,
        "source": SOURCE,
        "odds": "1.0"  # Let SmartBet.io use live Pinnacle odds
    }

# === SEND EMAIL TO SMARTBET.IO ===
def send_email_pick(pick):
    body = f"""SPORT: {pick['sport']}
EVENT: {pick['event']}
BET: {pick['bet']}
ODDS: {pick['odds']}
STAKE: {pick['stake']}
BOOK: {pick['book']}
SOURCE: {pick['source']}
"""
    msg = MIMEText(body)
    msg['Subject'] = f"New Pick: {pick['event']} - {pick['bet']}"
    msg['From'] = GMAIL_ADDRESS
    msg['To'] = SMARTBET_EMAIL

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, SMARTBET_EMAIL, msg.as_string())
        print(f"✅ Pick sent via email to SmartBet.io:\n{body}")
        return True
    except Exception as e:
        print(f"❌ Failed to send pick: {e}")
        return False

# === TELEGRAM HANDLER ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text:
        return
    if "Bet :" in text:
        pick = parse_alert(text)
        success = send_email_pick(pick)
        if success:
            await update.message.reply_text("✅ Pick sent to SmartBet.io via email!")
        else:
            await update.message.reply_text("❌ Failed to send pick.")

# === START FLASK + TELEGRAM BOT ===
if __name__ == '__main__':
    # Run Flask in a background thread
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))).start()

    # Run Telegram bot in main thread
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Telegram bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
