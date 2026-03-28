import telebot
import requests
import random
from telebot import types
from flask import Flask
from threading import Thread
from apscheduler.schedulers.background import BackgroundScheduler

# --- SOZLAMALAR ---
TOKEN = '7746900380:AAH80504854901432841724676_46a709'
ADMIN_ID = 505222809  # Sizning ID raqamingiz
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Reklama vaqtini boshqarish uchun
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
    bot_name = f"@{bot.get_me().username}"
    reklama_stili = [
        f"💰 Dollarni qayerda qimmatroq sotishni bilmayapsizmi? \n🏦 Barcha banklardagi real kurslarni bizda kuzating: {bot_name}",
        f"📊 Markaziy Bankning rasmiy kurslari va oltin narxlari har kuni yangilanadi! \n🚀 Botga o'ting: {bot_name}",
        f"🧮 Valyuta hisoblashda adashib ketyapsizmi? \nBizning qulay kalkulyatorimizdan foydalaning: {bot_name}",
        f"✨ Eng tezkor va aniq valyuta kursi boti! \n✅ USD, EUR, RUB va Oltin narxi bir joyda: {bot_name}",
        f"🏢 Bankka borishdan oldin kursni bizda tekshiring! \nEng foydali kurslarni ko'rsatib beramiz: {bot_name}"
    ]
    return random.choice(reklama_stili)

# --- AVTOMATIK REKLAMA YUBORISH (GURUHLARGA) ---
def run_group_marketing():
    groups = get_list("groups.txt")
    if not groups: return
    
    ad_text = generate_ai_ad()
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🚀 Botni ishga tushirish", url=f"https://t.me/{bot.get_me().username}?start=reklama"))
    
    for g_id in groups:
        try:
            bot.send_message(g_id, ad_text, reply_markup=markup)
        except: pass

# --- GURUHLARDA KALIT SO'ZLARNI TUTISH ---
@bot.message_handler(func=lambda m: m.chat.type != 'private' and any(word in m.text.lower() for word in ['dollar', 'kurs', 'narx', 'tilla', 'so\'m', 'valyuta']))
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
        gold = "1,150,000" # MB narxi
        
        text = f"✨ **BUGUNGI NARX-NAVOLAR** ✨\n"
        text += f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        text += f"🟡 **OLTIN (1 gr):** {gold} so'm\n\n"
        text += f"🇺🇸 **USD:** {usd} so'm\n"
        text += f"🇪🇺 **EUR:** {eur} so'm\n"
        text += f"🇷🇺 **RUB:** {rub} so'm\n"
        text += f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        text += f"📅 Sana: {r[0]['Date']}"
        return text
    except: return "⚠️ Ma'lumot yuklanmadi."

# --- ASOSIY MENYU ---
def main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🔄 Yangilash", "🏦 Banklar kursi", "🧮 Kalkulyator", "🌍 Boshqa valyutalar")
    if str(user_id) == str(ADMIN_ID):
        markup.add("📊 Statistika", "📢 Reklamani Yoqish", "🛑 To'xtatish")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.type == 'private':
        save_id("users.txt", message.chat.id)
        bot.send_message(message.chat.id, get_data(), parse_mode="Markdown", reply_markup=main_menu(message.chat.id))
    else:
        save_id("groups.txt", message.chat.id)
        bot.send_message(message.chat.id, "Bot guruhda faol! Kurslarni bilish uchun menga yozing.")

# --- KALKULYATOR ---
@bot.message_handler(func=lambda m: m.text == "🧮 Kalkulyator")
def calc_choice(m):
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(types.InlineKeyboardButton("🇺🇸 USD", callback_data="calc_USD"),
               types.InlineKeyboardButton("🇪🇺 EUR", callback_data="calc_EUR"),
               types.InlineKeyboardButton("🇷🇺 RUB", callback_data="calc_RUB"))
    bot.send_message(m.chat.id, "Qaysi valyutani so'mga aylantiramiz?", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith('calc_'))
def callback_calc(c):
    val = c.data.split('_')[1]
    bot.answer_callback_query(c.id)
    msg = bot.send_message(c.message.chat.id, f"{val} miqdorini kiriting (Masalan: 100):")
    bot.register_next_step_handler(msg, process_calc, val)

def process_calc(m, val):
    try:
        amt = float(m.text)
        r = requests.get("https://cbu.uz/uz/arkhiv-kursov-valyut/json/").json()
        rate = float(next(i['Rate'] for i in r if i['Ccy'] == val))
        bot.send_message(m.chat.id, f"✅ {amt:,.2f} {val} = **{amt*rate:,.2f} so'm**", parse_mode="Markdown")
    except: bot.
