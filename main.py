import os
import requests
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# === Environment Variables ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
SMARTBET_KEY = os.getenv("SMARTBET_KEY")
SPORT = os.getenv("SPORT", "SOCCER")
BOOK = os.getenv("BOOK", "PINNACLE")
STAKE = os.getenv("STAKE", "5")
BET_TYPE = os.getenv("BET_TYPE", "UNDER 0.5")
SOURCE = os.getenv("SOURCE", "smb.Vantage08>TelegramAlerts")

# === Telegram Handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is running and ready to forward bets to SmartBet.io!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text:
        return

    # Simple trigger detection: "Over/Under" or “Odds”
    if "Over/Under" in text and "Odds" in text:
        # Extract event name (you can refine this regex later)
        lines = text.split("\n")
        event_line = next((l for l in lines if "vs" in l), None)
        event = event_line.replace("vs", "-").strip() if event_line else "Unknown Match"

        # Send bet to SmartBet.io
        payload = {
            "key": SMARTBET_KEY,
            "sport": SPORT,
            "event": event,
            "bet": BET_TYPE,
            "odds": "auto",  # Smartbet will fetch Pinnacle odds
            "stake": STAKE,
            "book": BOOK,
            "source": SOURCE,
        }

        response = requests.post("https://smartbet.io/postpick.php", json=payload)
        if response.status_code == 200:
            await update.message.reply_text(f"✅ Bet placed for {event}")
        else:
            await update.message.reply_text(f"⚠️ Error placing bet: {response.text}")

# === Main ===
async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
