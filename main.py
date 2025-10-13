import os
import threading
import asyncio
import requests
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- Load environment variables ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
BET_TYPE = os.getenv("BET_TYPE")
BOOK = os.getenv("BOOK")
SPORT = os.getenv("SPORT")
STAKE = os.getenv("STAKE")
SMARTBET_KEY = os.getenv("SMARTBET_KEY")

# --- Flask web app (to keep Render alive) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Telegram bot is running successfully on Render!"

# --- Telegram bot handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot is live and ready to send SmartBet alerts!")

async def betinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test command to confirm environment variables are loaded correctly"""
    message = (
        f"📊 Current Configuration:\n"
        f"- Bet Type: {BET_TYPE}\n"
        f"- Book: {BOOK}\n"
        f"- Sport: {SPORT}\n"
        f"- Stake: {STAKE}\n"
        f"- SmartBet Key: {SMARTBET_KEY[:5]}****"
    )
    await update.message.reply_text(message)

# --- Function to fetch SmartBet data and send alerts ---
async def send_smartbet_alert(application: Application):
    try:
        url = f"https://api.smartbet.io/{SPORT}?book={BOOK}&betType={BET_TYPE}"
        headers = {"Authorization": SMARTBET_KEY}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()

        if not data:
            print("No SmartBet data found.")
            return

        message = f"⚽ SmartBet Alert ({SPORT})\n\n"
        for item in data[:5]:  # Example: show first 5 matches
            message += f"{item['home']} vs {item['away']} - {item['pick']} @ {item['odds']}\n"

        # Send to your Telegram bot (you can specify a chat_id here)
        await application.bot.send_message(chat_id=update.effective_chat.id, text=message)

    except Exception as e:
        print(f"Error sending alert: {e}")

# --- Telegram bot main function ---
async def main():
    app_bot = Application.builder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("betinfo", betinfo))

    print("🚀 Starting Telegram bot...")
    await app_bot.run_polling()

def run_telegram_bot():
    asyncio.run(main())

# --- Run both Flask and Telegram in parallel ---
if __name__ == '__main__':
    telegram_thread = threading.Thread(target=run_telegram_bot)
    telegram_thread.start()

    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
