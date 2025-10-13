# main.py
import os
import re
import requests
import threading
import asyncio
from flask import Flask
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

# -------------------------
# Configuration (via env)
# -------------------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # MUST match your Render env var
SMARTBET_KEY = os.getenv("SMARTBET_KEY")         # e.g. bcbwb-...
SPORT = os.getenv("SPORT", "SOCCER")
BET_TYPE = os.getenv("BET_TYPE", "UNDER 0.5")
BOOK = os.getenv("BOOK", "PINNACLE")
STAKE = os.getenv("STAKE", "5")
SOURCE = os.getenv("SOURCE", "smb.Vantage08>TelegramAlerts")

SMARTBET_URL = "https://smartbet.io/postpick.php"

# Simple memory of processed message ids to avoid duplicates while running
_processed_message_ids = set()
_MAX_PROCESSED = 1000

# -------------------------
# Small Flask app (health)
# -------------------------
app = Flask(__name__)

@app.route("/")
def health():
    return "Telegram → SmartBet bot is running!"

# -------------------------
# Helpers: parse alert text
# -------------------------
def find_event_line(text: str) -> str | None:
    """
    Return line containing "vs" (case-insensitive), cleaned to 'Home - Away'.
    """
    if not text:
        return None
    # split lines and normalize spaces
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for line in lines:
        # look for " vs " or " vs. " or " v " patterns
        low = line.lower()
        if " vs " in low or " vs. " in low or " v " in low:
            # normalize separators to " - "
            clean = re.sub(r"\s+v(?:s\.?|s)?\s+", " - ", line, flags=re.I)
            return clean.strip()
    # fallback: try a regex for something like "TeamA - TeamB"
    for line in lines:
        if "-" in line and len(line.split("-")) == 2:
            return line.strip().replace(" - ", " - ")
    return None

def is_under_half(text: str) -> bool:
    """
    Detect if message is about Under 0.5 (accepts variants: Under 0.5, Under 0.50, (Under 0.5), etc.)
    """
    if not text:
        return False
    return bool(re.search(r"under\s*0(?:\.?50?|\.?5)?", text, flags=re.I))

# -------------------------
# Main Telegram handler
# -------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return

    # avoid reacting to bot messages (including ourselves)
    if msg.from_user and msg.from_user.is_bot:
        return

    msg_id = (msg.chat.id, msg.message_id)
    if msg_id in _processed_message_ids:
        # already handled
        return

    # keep set size bounded
    _processed_message_ids.add(msg_id)
    if len(_processed_message_ids) > _MAX_PROCESSED:
        # simple pruning
        while len(_processed_message_ids) > _MAX_PROCESSED // 2:
            _processed_message_ids.pop()

    text = msg.text.strip()
    # Only proceed if the alert indicates Under 0.5
    if not is_under_half(text):
        # we only auto-bet Under 0.5 alerts
        return

    # Extract match/event line
    event = find_event_line(text)
    if not event:
        # If we couldn't find a 'vs' line, reply and skip to avoid wrong bets
        try:
            await msg.reply_text("⚠️ Could not detect match line (no 'vs' found). Bet not placed.")
        except Exception:
            pass
        return

    # Build SmartBet payload (omit odds so SmartBet uses Pinnacle live odds)
    payload = {
        "key": SMARTBET_KEY,
        "sport": SPORT,
        "event": event,
        "bet": BET_TYPE,
        "stake": STAKE,
        "book": BOOK,
        "source": SOURCE
    }

    # Send to SmartBet.io
    try:
        resp = requests.post(SMARTBET_URL, json=payload, timeout=10)
        # Log and respond in chat
        if resp.status_code == 200:
            # SmartBet usually returns JSON/text with status; include it in reply
            resp_text = resp.text
            try:
                await msg.reply_text(f"✅ Sent to SmartBet for:\n{event}\nResponse: {resp_text}")
            except Exception:
                pass
            print(f"[SMARTBET SUCCESS] event={event} resp={resp_text}")
        else:
            err = f"HTTP {resp.status_code}: {resp.text}"
            try:
                await msg.reply_text(f"❌ SmartBet failed for {event}: {err}")
            except Exception:
                pass
            print(f"[SMARTBET ERROR] event={event} {err}")
    except requests.RequestException as e:
        print(f"[SMARTBET EXC] event={event} error={e}")
        try:
            await msg.reply_text(f"❌ Network error sending to SmartBet: {e}")
        except Exception:
            pass

# -------------------------
# Startup: run Telegram bot in thread (works in Render)
# -------------------------
async def _run_application_async():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    # optional: small /status command
    async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Bot active — listening for Under 0.5 alerts.")
    app.add_handler(MessageHandler(filters.Command("status"), status_cmd))
    print("🚀 Telegram application initializing (polling)...")
    await app.initialize()
    # start polling (this will block until stopped)
    await app.start()
    await app.updater.start_polling()
    # keep application running
    await app.updater.wait_until_closed()
    await app.stop()
    await app.shutdown()

def start_telegram_in_thread():
    # create a fresh event loop for this thread (fixes Python 3.13 issue)
    def _target():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_run_application_async())
        finally:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
    t = threading.Thread(target=_target, daemon=True)
    t.start()

# -------------------------
# Entrypoint
# -------------------------
if __name__ == "__main__":
    # sanity checks
    missing = []
    if not TELEGRAM_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not SMARTBET_KEY:
        missing.append("SMARTBET_KEY")
    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        raise SystemExit(1)

    # start telegram bot thread
    start_telegram_in_thread()

    # start Flask (Render expects a web process listening on PORT)
    port = int(os.environ.get("PORT", "10000"))
    print(f"Starting Flask on port {port} (Render health endpoint)...")
    app.run(host="0.0.0.0", port=port)
