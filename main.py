import telebot
import smtplib
from email.mime.text import MIMEText

# === CONFIG ===
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
SENDER_EMAIL = "youremail@gmail.com"  # same email registered on SmartBet.io
APP_PASSWORD = "your_16_char_app_password"  # Gmail app password
SMARTBET_EMAIL = "picks@smartbet.io"
SMARTBET_SOURCE = "Kakason08"

bot = telebot.TeleBot(BOT_TOKEN)

def send_email_to_smartbet(sport, event, bet, odds, stake, book):
    """Send formatted SmartBet pick email"""
    body = f"""SPORT: {sport}
EVENT: {event}
BET: {bet}
ODDS: {odds}
STAKE: {stake}
BOOK: {book}
SOURCE: {SMARTBET_SOURCE}
"""

    msg = MIMEText(body)
    msg['Subject'] = f"SmartBet Pick: {event}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = SMARTBET_EMAIL

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, SMARTBET_EMAIL, msg.as_string())
        return "✅ Pick email sent successfully to SmartBet.io!"
    except Exception as e:
        return f"❌ Email sending failed: {str(e)}"

# === TELEGRAM BOT HANDLER ===
@bot.message_handler(commands=['sendpick'])
def handle_sendpick(message):
    bot.reply_to(message, "Please enter your pick in this format:\n\nSPORT|EVENT|BET|ODDS|STAKE|BOOK")

@bot.message_handler(func=lambda m: "|" in m.text)
def handle_pick(message):
    try:
        sport, event, bet, odds, stake, book = [x.strip() for x in message.text.split("|")]
        result = send_email_to_smartbet(sport, event, bet, odds, stake, book)
        bot.reply_to(message, result)
    except Exception as e:
        bot.reply_to(message, f"❌ Invalid format or error: {e}")

print("🤖 SmartBet Email Bot is running...")
bot.infinity_polling()
