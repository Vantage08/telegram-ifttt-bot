import os
import logging
import requests
from flask import Flask, request

# === CONFIG ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
IFTTT_WEBHOOK_URL = "https://maker.ifttt.com/trigger/telegram_alert/with/key/c6QsqQqCIl9LzH6X2Oo04yAbYvsAfrCLP44qy9_sCt2"
SMARTBET_EMAIL = "picks@smartbet.io"
SOURCE = "Kakason08>TelegramAlerts"

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


def send_telegram_message(chat_id, text):
    """Send Telegram confirmation."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})


def send_email_to_smartbet(message_text):
    """Send formatted alert to SmartBet via IFTTT webhook."""
    try:
        formatted_body = f"{message_text}\nSOURCE: {SOURCE}"
        r = requests.post(IFTTT_WEBHOOK_URL, json={"value1": formatted_body}, timeout=10)
        if r.status_code == 200:
            logging.info("📤 Sent to SmartBet via IFTTT successfully")
            return True
        logging.error(f"❌ IFTTT failed ({r.status_code}): {r.text}")
        return False
    except Exception as e:
        logging.error(f"Error sending to SmartBet: {e}")
        return False


@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    """Handle Telegram messages."""
    data = request.get_json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "").strip()

        logging.info(f"📩 Telegram message received: {text}")

        # Check if message is in SmartBet format
        required_keys = ["SPORT:", "EVENT:", "BET:", "ODDS:", "BOOK:"]
        if all(k in text for k in required_keys):
            new_lines = []
            odds = 1.03
            stake_fixed = False

            for line in text.splitlines():
                line = line.strip()

                if line.startswith("ODDS:"):
                    try:
                        current_odds = float(line.split("ODDS:")[1].strip())
                        if current_odds < 1.03:
                            new_lines.append("ODDS: 1.03")
                            odds = 1.03
                        else:
                            new_lines.append(f"ODDS: {current_odds}")
                            odds = current_odds
                    except ValueError:
                        new_lines.append("ODDS: 1.03")
                        odds = 1.03

                elif line.startswith("STAKE:"):
                    new_lines.append("STAKE: 5")
                    stake_fixed = True

                else:
                    new_lines.append(line)

            # Add stake if not present
            if not stake_fixed:
                new_lines.append("STAKE: 5")

            formatted_text = "\n".join(new_lines)

            # Send to SmartBet via IFTTT
            if send_email_to_smartbet(formatted_text):
                send_telegram_message(chat_id, f"✅ Sent to SmartBet.io (Stake: 5, Odds: {odds})")
            else:
                send_telegram_message(chat_id, "❌ Failed to send email to SmartBet. Check logs.")
        else:
            send_telegram_message(
                chat_id,
                "⚠️ Please follow the format:\n\nSPORT:\nEVENT:\nBET:\nODDS:\nBOOK:"
            )

    return {"ok": True}


@app.route("/", methods=["GET", "HEAD"])
def home():
    return "Telegram ↔ SmartBet Bot running", 200


if __name__ == "__main__":
    webhook_url = f"https://telegram-ifttt-bot.onrender.com/{BOT_TOKEN}"
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook", json={"url": webhook_url})
    app.run(host="0.0.0.0", port=10000)
