import telebot
import requests
import random
from telebot import types
from flask import Flask
from threading import Thread
from apscheduler.schedulers.background import BackgroundScheduler

# --- SOZLAMALAR (YANGI TOKEN BILAN) ---
TOKEN = '8606825506:AAHoLYaanIjoudJ5zDuhWsFkK-VG_FV29nk'
ADMIN_ID = 505222809 
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
scheduler = BackgroundScheduler()
scheduler.start()

# --- FAYLLAR BILAN ISHLASH (BAZA) ---
def get_list(file_name):
    try:
        with open(file_name, "r") as f:
            return f.read().splitlines()
    except FileNotFoundError:
        with open(file_name, "w") as f: return []
    except: return []

def save_id(file_name, target_id):
    ids = get_list(file_name)
    if str(target_id) not in ids:
        with open(file_name, "a") as f:
            f.write(str(target_id) + "\n")

# --- AI REKLAMA GENERATORI (FAQAT BOTNI REKLAMA QILADI) ---
def generate_ai_ad():
    bot_link = f"https://t.me/{bot.get_me().username}"
    reklama_stili = [
        f"💰 Dollarni qayerda qimmatroq sotishni bilmayapsizmi? \n🏦 Barcha banklardagi real kurslarni bizda kuzating: {bot_link}",
        f"📊 Markaziy Bankning rasmiy kurslari va oltin narxlari har kuni yangilanadi! \n🚀 Botga o'ting: {bot_link}",
        f"🧮 Valyuta hisoblashda adashib ketyapsizmi? \nBizning qulay kalkulyatorimizdan foydalaning: {bot_link}",
        f"✨ Eng tezkor va aniq valyuta kursi boti! \n✅ USD, EUR, RUB va Oltin narxi bir joyda: {bot_link}",
        f"🏢 Bankka borishdan oldin kursni bizda tekshiring! \nEng foydali kurslarni ko'rsatib beramiz: {bot_link}"
    ]
    return random.choice(reklama_stili)

# --- AVTOMATIK REKLAMA YUBORISH (GURUHLARGA) ---
def run_group_marketing():
    groups = get_list("groups.txt")
    if not groups: return
    
    ad_text = generate_ai_ad()
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🚀 Botga kirish", url=f"https://t.me/{bot.get_me().username}?start=reklama"))
    
    for g_id in groups:
        try:
            bot.send_message(g_id, ad_text, reply_markup=markup)
        except: pass

# --- GURUHLARDA KALIT SO'ZLARNI TUTISH ---
@bot.message_handler(func=lambda m: m.chat.type != 'private' and any(word in m.text.lower() for word in ['dollar', 'kurs', 'narx', 'tilla', 'valyuta', 'sum']))
def group_reply(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💰 Shaxsiyda ko'rish", url=f"https://t.me/{bot.get_me().username}?start=info"))
    bot.reply_to(message, "Barcha kurslar va oltin narxini shaxsiy xabaringizda ko'rish uchun pastdagi tugmani bosing! 👇", reply_markup=markup)

# --- MA'LUMOTLARNI OLISH (CBU API) ---
def get_data():
    try:
        url = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/"
        r = requests.get(url).json()
        usd = next(i['Rate'] for i in r if i['Ccy'] == 'USD')
        eur = next(i['Rate'] for i in r if i['Ccy'] == 'EUR')
        rub = next(i['Rate'] for i in r if i['Ccy'] == 'RUB')
        
        text = f"✨ **BUGUNGI NARX-NAVOLAR** ✨\n"
        text += f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        text += f"🇺🇸 **USD:** {usd} so'm\n"
        text += f
