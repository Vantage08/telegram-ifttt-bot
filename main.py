import telebot
import requests
import re
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
IFTTT_EVENT = "telegram_alert"
IFTTT_KEY = "c6QsqQqCIl9LzH6X2Oo04yAbYvsAfrCLP44qy9_sCt2"

bot = telebot.TeleBot(BOT_TOKEN)

def extract_match_name(text):
    # Finds the line containing "vs"
    lines = text.split('\n')
    for line in lines:
        if " vs " in line.lower():
            return line.strip()
    return None

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    match_name = extract_match_name(message.text)
    if match_name:
        requests.post(
            f"https://maker.ifttt.com/trigger/{IFTTT_EVENT}/with/key/{IFTTT_KEY}",
            json={"value1": match_name}
        )
        bot.reply_to(message, f"📨 Match sent to IFTTT:\n{match_name}")
    else:
        bot.reply_to(message, "⚠️ No match found in this message.")

print("🤖 Bot is running and listening for Telegram messages...")
bot.polling(none_stop=True)