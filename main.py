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

# ============================================================
# ENVIRONMENT CONFIGURATION (Render variables)
# ============================================================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
IFTTT_URL = os.getenv("IFTTT_WEBHOOK_URL")
SMARTBET_KEY = os.getenv("SMARTBET_KEY", "bcbwb-4d65eeb3-05af-4eb2-8cc7-6216f6622d22")
SPORT = os.getenv("SPORT", "SOCCER")
BOOK = os.getenv("BOOK", "PINNACLE")
STAKE = os.getenv("STAKE", "5")
SOURCE = os.getenv("SOURCE", "smb.Vantage08>TelegramAlerts")

# ============================================================
# FLASK HEALTH ENDPOINT (Render requires this)
# ============================================================
app = Flask(__name__)

@app.route("/")
def health():
    return "Telegram → IFTTT → SmartBet bot is running!"

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def find_event_line(text: str):
    """Finds the line containing 'vs' or similar pattern and normalizes it."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for line in lines:
        if " vs " in line.lower() or re.search(r"\bv\s\b", line, re.I):
            return re.sub(r"\s+v(?:s\.?|s)?\s+", " - ", line, flags=re.I)
    return None

def find_bet_type(text: str):
    """
    Detects a line like 'Bet : Under 0.5' or 'Bet: Over 1.5'
    """
    match = re.search(r"Bet\s*:\s*([A-Za-z0-9\.\s]+)", text, flags=re.I)
    if match:
        return match.group(1).strip().upper()
    # fallback default
    return "UNDER 0.5"

# ============================================================
# TELEGRAM MESSAGE HANDLER
# ============================================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text or msg.from_user.is_bot:
        return

    text = msg.text.strip()
    event = find_event_line(text)
    if not event:
        return

    bet_type = find_bet_type(text)

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
        # send to IFTTT webhook
        res = requests.post(IFTTT_URL, json=payload, timeout=10)
        if res.status_code == 200:
            await msg.reply_text(f"✅ Sent to IFTTT:\n{event}\nBet: {bet_type}")
            print(f"[OK] Sent to IFTTT for event: {event} ({bet_type})")
        else:
            await msg.reply_text(f"❌ IFTTT Error: {res.status_code}")
            print(f"[ERR] IFTTT returned {res.status_code}: {res.text}")
    except Exception as e:
        await msg.reply_text(f"❌ Error sending to IFTTT: {e}")
        print(f"[EXC] {e}")

# ============================================================
# OPTIONAL COMMAND: /status
# ============================================================
async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"SPORT={SPORT}  STAKE={STAKE}  BOOK={BOOK}\nSource={SOURCE}"
    )

# ============================================================
# TELEGRAM BOT BACKGROUND LOOP (FIXED FOR RENDER)
# ============================================================
async def _run_app_async():
    app_bot = Application.builder().token(TELEGRAM_TOKEN).build()
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app_bot.add_handler(CommandHandler("status", status_cmd))
    print("🚀 Telegram bot initialized.")

    # run_polling safely without signal handlers (Render fix)
    await app_bot.initialize()
    await app_bot.start()
    print("✅ Bot polling started.")
    await app_bot.updater.start_polling()
    await asyncio.Event().wait()   # keep alive forever

def start_telegram_thread():
    threading.Thread(target=lambda: asyncio.run(_run_app_async()), daemon=True).start()

# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    if not TELEGRAM_TOKEN or not IFTTT_URL:
        print("❌ ERROR: Missing TELEGRAM_BOT_TOKEN or IFTTT_WEBHOOK_URL")
        raise SystemExit(1)

    start_telegram_thread()

    port = int(os.environ.get("PORT", "10000"))
    print(f"🌐 Starting Flask health check on port {port} ...")
    app.run(host="0.0.0.0", port=port)
