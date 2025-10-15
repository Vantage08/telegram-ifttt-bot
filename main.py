from flask import Flask, request
import telegram
import os

app = Flask(__name__)

# Load environment variables
TOKEN = os.environ.get("TELEGRAM_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

bot = telegram.Bot(token=TOKEN)

# --- Webhook route ---
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    chat_id = update.message.chat.id
    text = update.message.text

    # Simple echo for test
    bot.send_message(chat_id=chat_id, text=f"You said: {text}")
    return "ok", 200

@app.route("/", methods=["GET"])
def home():
    return "Bot is running fine!", 200

if __name__ == "__main__":
    # Set webhook (so Telegram knows where to send updates)
    webhook_url = f"{WEBHOOK_URL}/{TOKEN}"
    bot.delete_webhook()
    bot.set_webhook(url=webhook_url)
    print("🤖 Webhook set successfully!")
    print(f"🌐 Telegram bot is running at {webhook_url}...")
    app.run(host="0.0.0.0", port=10000)
