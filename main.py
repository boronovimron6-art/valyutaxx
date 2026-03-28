import telebot
import requests
import random
from telebot import types
from flask import Flask
from threading import Thread
from apscheduler.schedulers.background import BackgroundScheduler

# --- SOZLAMALAR ---
TOKEN = '7746900380:AAH80504854901432841724676_46a709'
ADMIN_ID = 505222809 
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
scheduler = BackgroundScheduler()
scheduler.start()

# --- FAYLLAR BILAN ISHLASH ---
def get_list(file_name):
    try:
        with open(file_name, "r") as f: return f.read().splitlines()
    except: return []

def save_id(file_name, target_id):
    ids = get_list(file_name)
    if str(target_id) not in ids:
        with open(file_name, "a") as f: f.write(str(target_id) + "\n")

# --- KURSLARNI OLISH ---
def get_data():
    try:
        r = requests.get("https://cbu.uz/uz/arkhiv-kursov-valyut/json/").json()
        usd = next(i['Rate'] for i in r if i['Ccy'] == 'USD')
        eur = next(i['Rate'] for i in r if i['Ccy'] == 'EUR')
        rub = next(i['Rate'] for i in r if i['Ccy'] == 'RUB')
        return f"💰 **MB rasmiy kurslari:**\n\n🇺🇸 1 USD = {usd} so'm\n🇪🇺 1 EUR = {eur} so'm\n🇷🇺 1 RUB = {rub} so'm\n\n📅 Sana: {r[0]['Date']}"
    except: return "⚠️ Ma'lumot olishda xatolik."

# --- ASOSIY MENYU ---
def main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("📊 Kurslarni ko'rish"), types.KeyboardButton("🧮 Kalkulyator"))
    markup.add(types.KeyboardButton("🏦 Banklar kursi"), types.KeyboardButton("🌍 Boshqa valyutalar"))
    if str(user_id) == str(ADMIN_ID):
        markup.add(types.KeyboardButton("📈 Statistika"), types.KeyboardButton("📢 Reklamani Yoqish"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    save_id("users.txt" if message.chat.type == 'private' else "groups.txt", message.chat.id)
    bot.send_message(message.chat.id, "👋 Xush kelibsiz! Kerakli bo'limni tanlang:", reply_markup=main_menu(message.chat.id))

# --- ODDY TUGMALAR ---
@bot.message_handler(func=lambda m: m.text == "📊 Kurslarni ko'rish")
def show_rates(m):
    bot.send_message(m.chat.id, get_data(), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📈 Statistika" and str(m.chat.id) == str(ADMIN_ID))
def show_stats(m):
    u = len(get_list("users.txt"))
    g = len(get_list("groups.txt"))
    bot.send_message(ADMIN_ID, f"👤 Obunachilar: {u}\n👥 Guruhlar: {g}")

# --- SERVER ---
@app.route('/')
def h(): return "Active"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.infinity_polling()
