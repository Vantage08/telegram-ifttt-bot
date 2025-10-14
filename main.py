import os
import json
import smtplib
from email.message import EmailMessage
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# === CONFIGURATION ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
SMARTBET_EMAIL = "picks@smartbet.io"

SPORT = "Football"
STAKE = 5
BOOK = "Pinnacle"
SOURCE = os.getenv("SOURCE", "Kakason08")  # Your SmartBet.io source

LOG_FILE = os.getenv("LOG_FILE", "smartbet_picks.log")

# === FLASK APP ===
app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)
application = Application.builder().bot(bot).build()

# === PARSE TELEGRAM ALERT ===
def parse_alert(message_text):
    lines = message_text.split("\n")
    event = None
    bet = None

    # Bet type
    for line in lines:
        if line.lower().startswith("bet :"):
            bet = line.split(":", 1)[1].strip()
            break

    # Event
    for line in lines:
        if " vs " in line.lower():
            event = line.strip().replace(" vs ", " - ").replace(" VS ", " - ")
            break

    return {"event": event or "Unknown Event", "bet": bet or "UNKNOWN"}

# === SEND PICK VIA EMAIL ===
def send_pick_email(event, bet):
    body = f"""SPORT: {SPORT}
EVENT: {event}
BET: {bet}
ODDS: 1.0
STAKE: {STAKE}
BOOK: {BOOK}
SOURCE: {SOURCE}
"""
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = f"SmartBet.io Pick - {event}"
        msg["From"] = GMAIL_ADDRESS
        msg["To"] = SMARTBET_EMAIL

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            smtp.send_message(msg)

        # Log the pick
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps({"event": event, "bet": bet}) + "\n")

        print(f"✅ Pick sent via email: {body}")
        return True
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False

# === TELEGRAM HANDLER ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text:
        return
    if "Bet :" in text:
        alert_data = parse_alert(text)
        success = send_pick_email(alert_data["event"], alert_data["bet"])
        if success:
            await update.message.reply_text("✅ Pick sent to SmartBet.io via email!")
        else:
            await update.message.reply_text("❌ Failed to send pick to SmartBet.io.")

application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# === WEBHOOK ROUTE ===
@app.route(f'/{BOT_TOKEN}', methods=["POST"])
async def telegram_webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, bot)
    await application.update_queue.put(update)
    return "OK", 200

# === HEALTH CHECK ===
@app.route('/')
def index():
    return "Bot is running", 200

# === START FLASK APP ===
if __name__ == "__main__":
    import asyncio

    async def setup_webhook():
        await bot.delete_webhook()
        await bot.set_webhook(url=f"https://YOUR_RENDER_APP_URL/{BOT_TOKEN}")
        print("🤖 Webhook set successfully!")

    asyncio.run(setup_webhook())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
