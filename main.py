import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, filters
import asyncio

# === Load environment variables ===
TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN not found in environment variables!")

bot = Bot(token=TOKEN)
app = Flask(__name__)

# === Handle incoming Telegram messages ===
async def handle_message(update: Update, context):
    chat_id = update.effective_chat.id
    text = update.message.text
    await context.bot.send_message(chat_id=chat_id, text=f"You said: {text}")

# === Set webhook properly (async) ===
async def set_webhook():
    await bot.delete_webhook()
    await bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
    print(f"🤖 Webhook set to {WEBHOOK_URL}/{TOKEN}")

# === Flask route to handle Telegram webhook ===
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    asyncio.run(handle_message(update, None))
    return "OK", 200

@app.route('/')
def home():
    return "Telegram IFTTT Bot is running!", 200

# === Start everything ===
if __name__ == "__main__":
    asyncio.run(set_webhook())
    print(f"🌐 Telegram bot is running at {WEBHOOK_URL}/{TOKEN} ...")
    app.run(host="0.0.0.0", port=10000)
