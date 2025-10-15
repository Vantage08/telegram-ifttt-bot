import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # your render URL, e.g., https://telegram-ifttt-bot.onrender.com

app = Flask(__name__)

# Initialize bot and app
bot = Bot(token=TOKEN)
application = Application.builder().token(TOKEN).build()


# --- Handlers ---
async def start(update: Update, context):
    await update.message.reply_text("👋 Hello! Your Telegram bot is now connected and live.")


async def echo(update: Update, context):
    user_message = update.message.text
    await update.message.reply_text(f"✅ Received: {user_message}")


application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))


# --- Flask routes ---
@app.route("/")
def home():
    return "🤖 Bot is live on Render!", 200


@app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    """Receive updates from Telegram"""
    try:
        update = Update.de_json(request.get_json(force=True), bot)
        await application.process_update(update)
    except Exception as e:
        print(f"❌ Error handling update: {e}")
    return "ok", 200


# --- Set webhook ---
if __name__ == "__main__":
    import asyncio

    async def set_webhook():
        await bot.delete_webhook()
        await bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
        print(f"🤖 Webhook set to {WEBHOOK_URL}/{TOKEN}")

    asyncio.run(set_webhook())

    print("🌐 Telegram bot is running on Render...")
    app.run(host="0.0.0.0", port=10000)
