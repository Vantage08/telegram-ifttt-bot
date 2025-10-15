import os
import smtplib
from email.mime.text import MIMEText
from flask import Flask, request, abort
import asyncio
from telegram import Bot, Update

# Environment variables
TOKEN = os.environ.get("TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

if not TOKEN or not WEBHOOK_URL or not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
    raise Exception("Missing one or more required environment variables!")

bot = Bot(token=TOKEN)
app = Flask(__name__)

# --- Flask route matching the webhook URL exactly ---
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    if request.method == "POST":
        update_data = request.get_json()
        if not update_data:
            abort(400)
        asyncio.run(handle_update(update_data))
        return "OK", 200
    else:
        abort(403)

# --- Handle incoming Telegram messages ---
async def handle_update(update_data):
    update = Update.de_json(update_data, bot)
    if update.message:
        text = update.message.text
        # Send pick to Smartbet.io email
        send_pick_email(text)
        await bot.send_message(chat_id=update.message.chat_id, text="Pick submitted!")

# --- Send pick to Smartbet.io via Gmail ---
def send_pick_email(pick_text):
    # Fixed parameters for Pinnacle and stake 5
    subject = "Automated Pick Submission"
    body = f"""SPORT: Football
EVENT: {pick_text}
BET: {pick_text}
ODDS: 1.0
STAKE: 5
BOOK: Pinnacle
SOURCE: Kakason08
"""
    msg = MIMEText(body)
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = "picks@smartbet.io"
    msg["Subject"] = subject

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.send_message(msg)

# --- Set webhook on startup ---
async def setup_webhook():
    # Delete any previous webhook
    await bot.delete_webhook()
    # Set new webhook
    await bot.set_webhook(url=WEBHOOK_URL)
    print(f"🤖 Webhook set to {WEBHOOK_URL}")

if __name__ == "__main__":
    asyncio.run(setup_webhook())
    print("🌐 Telegram bot is running on Render...")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
