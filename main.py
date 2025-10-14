import os
import smtplib
from email.mime.text import MIMEText
from flask import Flask, request
from telegram import Update, Bot
import asyncio

# === CONFIGURATION ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")        # Your Gmail address
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")  # Gmail App Password
SMARTBET_EMAIL = "picks@smartbet.io"
SOURCE = "Kakason08"
STAKE = "5"
ODDS = "0.0"   # Let SmartBet.io use Pinnacle odds
BOOK = "PINNACLE"

# === INITIALIZE ===
app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)

# === PARSE TELEGRAM ALERT ===
def parse_alert(text):
    lines = text.split("\n")
    event = None
    bet = None
    for line in lines:
        if line.lower().startswith("bet :"):
            bet = line.split(":")[1].strip()
        if " vs " in line.lower():
            event = line.strip().replace(" vs ", " - ").replace(" VS ", " - ")
    return event or "Unknown Event", bet or "UNKNOWN"

# === SEND EMAIL TO SMARTBET.IO ===
def send_email(event, bet):
    body = f"""SPORT: Football
EVENT: {event}
BET: {bet}
ODDS: {ODDS}
STAKE: {STAKE}
BOOK: {BOOK}
SOURCE: {SOURCE}"""
    
    msg = MIMEText(body)
    msg["Subject"] = f"Pick Submission: {event}"
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = SMARTBET_EMAIL

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, SMARTBET_EMAIL, msg.as_string())
        server.quit()
        print(f"✅ Email sent to SmartBet.io:\n{body}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

# === TELEGRAM WEBHOOK HANDLER ===
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    asyncio.create_task(handle_message(update))
    return "OK", 200

async def handle_message(update: Update):
    text = update.message.text if update.message else None
    if not text:
        return

    if "Bet :" in text:
        event, bet = parse_alert(text)
        success = send_email(event, bet)
        reply_text = "✅ Pick sent to SmartBet.io!" if success else "❌ Failed to send pick."
        await bot.send_message(chat_id=update.message.chat_id, text=reply_text)

# === FLASK HEALTH CHECK ===
@app.route("/")
def index():
    return "Bot is running", 200

# === SET TELEGRAM WEBHOOK ===
async def setup_webhook():
    webhook_url = f"https://telegram-ifttt-bot.onrender.com/{BOT_TOKEN}"
    await bot.delete_webhook()
    await bot.set_webhook(webhook_url)
    print("🌐 Webhook set successfully!")

# === RUN FLASK + SETUP WEBHOOK ===
if __name__ == "__main__":
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(setup_webhook())
    print("🌐 Flask server running...")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
