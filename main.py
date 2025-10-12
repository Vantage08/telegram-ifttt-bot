import telebot
import requests
import re
import os

# === Environment Variables ===
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Your Telegram bot token
SMARTBET_KEY = os.getenv("SMARTBET_KEY", "bcbwb-4d65eeb3-05af-4eb2-8cc7-6216f6622d22")
IFTTT_WEBHOOK_URL = os.getenv("IFTTT_WEBHOOK_URL", "https://maker.ifttt.com/trigger/telegram_alert/with/key/c6QsqQqCIl9LzH6X2Oo04yAbYvsAfrCLP44qy9_sCt2")

# === Default Betting Config ===
SPORT = "SOCCER"
BET = "UNDER 0.5"
STAKE = "5"
BOOK = "PINNACLE"
SOURCE = "smb.Vantage08>TelegramAlerts"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

def extract_event(message_text):
    """Extracts match name line containing 'vs'."""
    lines = message_text.split('\n')
    for line in lines:
        if " vs " in line.lower():
            return line.strip()
    return None

def send_to_smartbet(event_name):
    """Send data to Smartbet.io via POST."""
    url = "https://smartbet.io/postpick.php"
    payload = {
        "key": SMARTBET_KEY,
        "sport": SPORT,
        "event": event_name,
        "bet": BET,
        "stake": STAKE,
        "book": BOOK,
        "source": SOURCE
    }
    try:
        response = requests.post(url, json=payload)
        print("✅ Sent to Smartbet:", response.text)
    except Exception as e:
        print("❌ Error sending to Smartbet:", e)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text.strip()
    event_name = extract_event(text)

    if event_name:
        # Format for IFTTT display
        formatted_text = f"/ifttt\n{text}"
        requests.post(IFTTT_WEBHOOK_URL, json={"value1": formatted_text})
        print("📩 Sent to IFTTT:", formatted_text)

        # Send bet to Smartbet
        send_to_smartbet(event_name)
        bot.reply_to(message, f"✅ Bet sent for event:\n{event_name}")
    else:
        print("⚠️ No event detected in message.")

print("🤖 Bot running...")
bot.polling(non_stop=True)
