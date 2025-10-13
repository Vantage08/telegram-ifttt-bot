# main.py
import os
import re
import json
import requests
import threading
import asyncio
from flask import Flask
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

# ---------------------
# Environment variables
# ---------------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
IFTTT_URL = os.getenv("IFTTT_WEBHOOK_URL")
SMARTBET_KEY = os.getenv("SMARTBET_KEY", "bcbwb-4d65eeb3-05af-4eb2-8cc7-6216f6622d22")
SPORT = os.getenv("SPORT", "SOCCER")
BOOK = os.getenv("BOOK", "PINNACLE")
STAKE = os.getenv("STAKE", "5")
SOURCE = os.getenv("SOURCE", "smb.Vantage08>TelegramAlerts")

# ---------------------
# Flask for Render ping
# ---------------------
app = Flask(__name__)

@app.route("/")
def health():
    return "Telegram → IFTTT → SmartBet bot is running!"

# ---------------------
# Helper functions
# ---------------------
def find_event_line(text: str) -> str | None:
    """Find a line with 'vs' and normalize."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for line in lines:
        if " vs " in line.lower():
            return re.sub(r"\s+v(?:s\.?|s)?\s+", " - ", line, flags=re.I)
    return None

def find_bet_type(text: str) -> str:
    """Find line starting with Bet: ..."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for line in lines:
        if line.lower().startswith("bet"):
            # extract after ':'
            parts = line.split(":", 1)
            if len(parts) > 1:
                return parts[1].strip()
    # fallback default
    return "UNDER 0.5"

# ---------------------
# Telegram handler
# ---------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text or msg.from_user.is_bot:
        return

    text = msg.text.strip()
    event = find_event_line(text)
    bet_type = find_bet_type(text)

    if not event:
        return  # skip if no event line found

    payload = {
        "key": SMARTBET_KEY,
        "sport": SPORT,
        "event": event,
        "bet": bet_type,
        "stake": STAKE,
        "book": BOOK,
        "source": SOURCE
    }

    try:
        res = requests.post(IFTTT_URL, json=payload, timeout=10)
        if res.status_code == 200:
            await msg.reply_text(f"✅ Sent to IFTTT:\n{event}\nBet: {bet_type}")
            print(f"[OK] {event} | Bet: {bet_type}")
        else:
            await msg.reply_text(f"❌ IFTTT Error: {res.status_code}")
            print(f"[ERR] IFTTT {res.status_code}: {res.text}")
    except Exception as e:
        await msg.reply_text(f"❌ Error sending to IFTTT: {e}")
        print(f"[EXC] {e}")

# /status command
async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"SPORT={SPORT} STAKE={STAKE} BOOK={BOOK}"
    )

# ---------------------
# Run Telegram bot
# ---------------------
async def _run_app_async():
    app_bot = Application.builder().token(TELEGRAM_TOKEN).build()
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app_bot.add_handler(CommandHandler("status", status_cmd))
    print("🚀 Telegram bot initialized.")
    await app_bot.run_polling()

def start_telegram_thread():
    def _target():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_run_app_async())
    threading.Thread(target=_target, daemon=True).start()

# ---------------------
# Entrypoint
# ---------------------
if __name__ == "__main__":
    if not TELEGRAM_TOKEN or not IFTTT_URL:
        print("ERROR: Missing TELEGRAM_BOT_TOKEN or IFTTT_WEBHOOK_URL")
        raise SystemExit(1)

    start_telegram_thread()
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
