import os
import re
import logging
from flask import Flask, request
import requests

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
IFTTT_WEBHOOK_URL = os.getenv("IFTTT_WEBHOOK_URL", "https://maker.ifttt.com/trigger/smartbet_alert/json")

# === CONFIGURATION ===
FIXED_ODDS = "1.03"
FIXED_STAKE = "5"
FIXED_BOOK = "Pinnacle"
FIXED_SOURCE = "Kakason08>TelegramAlerts"
FIXED_SPORT = "Football"

logging.basicConfig(level=logging.INFO)


def clean_text(text: str) -> str:
    """Remove emojis, flags, and extra symbols."""
    text = re.sub(r"[^\x00-\x7F]+", " ", text)  # Remove non-ASCII
    text = re.sub(r"\(.*?\)", "", text)  # Remove parentheses content
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_alert(message: str) -> dict:
    """Extract bet details from the Telegram alert."""
    lines = message.strip().split("\n")
    bet = ""
    event = ""

    # Find Bet line
    for line in lines:
        if line.lower().startswith("bet"):
            bet = clean_text(line.split(":")[-1].strip())
        elif "vs" in line.lower():
            event = clean_text(line)
            break

    return {
        "sport": FIXED_SPORT,
        "event": event or "Unknown Event",
        "bet": bet or "Unknown Bet",
        "odds": FIXED_ODDS,
        "stake": FIXED_STAKE,
        "book": FIXED_BOOK,
        "source": FIXED_SOURCE,
    }


def format_smartbet_email(data: dict) -> str:
    """Format SmartBet.io email body."""
    return (
        f"SPORT: {data['sport']}\n"
        f"EVENT: {data['event']}\n"
        f"BET: {data['bet']}\n"
        f"ODDS: {data['odds']}\n"
        f"STAKE: {data['stake']}\n"
        f"BOOK: {data['book']}\n"
        f"SOURCE: {data['source']}"
    )


@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def telegram_webhook():
    """Handle incoming Telegram messages."""
    data = request.get_json()

    if "message" in data and "text" in data["message"]:
        message_text = data["message"]["text"]

        parsed = parse_alert(message_text)
        email_body = format_smartbet_email(parsed)

        # Send to IFTTT
        payload = {"value1": email_body}
        requests.post(IFTTT_WEBHOOK_URL, json=payload)

        chat_id = data["message"]["chat"]["id"]
        reply = f"✅ Sent to SmartBet.io (Stake: {parsed['stake']}, Odds: {parsed['odds']})"
        requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", params={
            "chat_id": chat_id,
            "text": reply
        })

    return {"ok": True}


@app.route("/")
def home():
    return "Telegram → SmartBet.io bot is running ✅"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
