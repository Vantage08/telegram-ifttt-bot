import os
import smtplib
from email.message import EmailMessage
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import re

# === CONFIGURATION ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
SMARTBET_EMAIL = "picks@smartbet.io"

SOURCE = "Kakason08"
STAKE = 5
BOOK = "Pinnacle"
ODDS = 1.0  # SmartBet.io will use live Pinnacle odds

# Flask app for webhook health check
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running", 200

# === PARSE TELEGRAM ALERT ===
def parse_alert(message_text):
    """
    Extract event and bet from Telegram alert.
    """
    event = None
    bet = None

    # Bet line (e.g., "Bet : Under 0.5")
    match_bet = re.search(r"Bet\s*:\s*(.+)", message_text, re.IGNORECASE)
    if match_bet:
        bet = match_bet.group(1).strip()

    # Event line (looking for "TeamA vs TeamB")
    match_event = re.search(r"(.+?)\s+vs\s+(.+)", message_text, re.IGNORECASE)
    if match_event:
        event = match_event.group(0).strip()

    return {"event": event or "Unknown Event", "bet": bet or "UNKNOWN"}

# === SEND PICK VIA EMAIL TO SMARTBET.IO ===
def send_email_pick(event, bet):
    """
    Sends the pick to SmartBet.io via email.
    """
    msg = EmailMessage()
    msg['Subject'] = f"Pick: {event} - {bet}"
    msg['From'] = GMAIL_ADDRESS
    msg['To'] = SMARTBET_EMAIL

    body = (
        f"SPORT: Football\n"
        f"EVENT: {event}\n"
        f"BET: {bet}\n"
        f"ODDS: {ODDS}\n"
        f"STAKE: {STAKE}\n"
        f"BOOK: {BOOK}\n"
        f"SOURCE: {SOURCE}"
    )
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            smtp.send_message(msg)
        print(f"✅ Pick sent via email: {event} - {bet}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

# === TELEGRAM HANDLER ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text:
        return

    # Only process messages containing a bet
    if "Bet :" in text:
        alert_data = parse_alert(text)
        success = send_email_pick(alert_data["event"], alert_data["bet"])
        if success:
            await update.message.reply_text(f"✅ Pick sent to SmartBet.io via email!")
        else:
            await update.message.reply_text("❌ Failed to send pick via email.")

# === START FLASK + TELEGRAM BOT ===
if __name__ == '__main__':
    import threading

    # Run Flask in a background thread for health check
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))).start()

    # Run Telegram bot in main thread
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Telegram bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
