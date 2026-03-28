import telebot
import requests
from telebot import types
from flask import Flask
from threading import Thread

# --- SOZLAMALAR ---
TOKEN = '8606825506:AAHoLYaanIjoudJ5zDuhWsFkK-VG_FV29nk'
ADMIN_ID = 505222809 
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# --- KURSLARNI OLISH ---
def get_data():
    try:
        url = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/"
        r = requests.get(url).json()
        usd = next(i['Rate'] for i in r if i['Ccy'] == 'USD')
        eur = next(i['Rate'] for i in r if i['Ccy'] == 'EUR')
        rub = next(i['Rate'] for i in r if i['Ccy'] == 'RUB')
        return f"💰 **Markaziy Bank kurslari:**\n\n🇺🇸 1 USD = {usd} so'm\n🇪🇺 1 EUR = {eur} so'm\n🇷🇺 1 RUB = {rub} so'm"
    except:
        return "⚠️ Ma'lumot olishda xatolik yuz berdi."

# --- ASOSIY MENYU ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("📊 Kurslarni ko'rish"))
    markup.add(types.KeyboardButton("📈 Statistika")) # Siz bosayotgan tugma
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "👋 Salom! Bot ishga tushdi.", reply_markup=main_menu())

@bot.message_handler(func=lambda m: True)
def handle_messages(message):
    if message.text == "📊 Kurslarni ko'rish":
        bot.send_message(message.chat.id, get_data(), parse_mode="Markdown")
    elif message.text == "📈 Statistika":
        bot.send_message(message.chat.id, "📊 Bot hozircha test rejimida ishlamoqda.")
    else:
        # Bot xabarni shunchaki qaytarmasligi uchun buni o'chirib qo'yamiz yoki o'zgartiramiz
        bot.send_message(message.chat.id, "Tushunmadim. Menyu tugmalaridan foydalaning.")

# --- RENDER UCHUN SERVER ---
@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.infinity_polling()
