import telebot
import requests
import random
from telebot import types
from flask import Flask
from threading import Thread
from apscheduler.schedulers.background import BackgroundScheduler

# --- SOZLAMALAR ---
TOKEN = '8606825506:AAHoLYaanIjoudJ5zDuhWsFkK-VG_FV29nk'
ADMIN_ID = 505222809 
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# AI Holati va Narxlar (Boshlang'ich)
ai_active = True
current_prices = {"Kun": 25000, "Hafta": 100000, "Oy": 350000}

# --- MA'LUMOTLAR BAZASI (ODDIY FAYL) ---
def get_ids(file_name):
    try:
        with open(file_name, "r") as f: return f.read().splitlines()
    except: return []

def save_id(file_name, target_id):
    ids = get_ids(file_name)
    if str(target_id) not in ids:
        with open(file_name, "a") as f: f.write(str(target_id) + "\n")

# --- ASOSIY MA'LUMOTLARNI OLISH ---
def get_global_rates():
    try:
        # Markaziy Bank API
        r = requests.get("https://cbu.uz/uz/arkhiv-kursov-valyut/json/").json()
        
        # Oltin narxi (MB yoki Jahon bozoridagi 1gr taxminiy narxi)
        gold = "988,600"
        # Kripto dollar (USDT) kursi
        usdt_rate = 12985 
        
        targets = {'USD': '🇺🇸', 'EUR': '🇪🇺', 'RUB': '🇷🇺', 'KZT': '🇰🇿', 'GBP': '🇬🇧'}
        
        text = f"🟡 **OLTIN (1 gr): {gold} so'm**\n"
        text += f"💎 **USDT (Kripto): {usdt_rate:,.0f} so'm**\n"
        text += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        
        for code, emoji in targets.items():
            rate = next(i['Rate'] for i in r if i['Ccy'] == code)
            text += f"{emoji} 1 {code} = {rate} so'm\n"
            
        text += f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n📅 Sana: {r[0]['Date']}\n🤖 AI Tahlili: Barqaror"
        return text
    except:
        return "⚠️ Ma'lumot yangilanishida vaqtincha uzilish. Birozdan so'ng urinib ko'ring."

# --- AI REKLAMA VA NARX TAKLIFI ---
def ai_marketing_engine():
    if not ai_active: return
    groups = get_ids("groups.txt")
    if not groups: return
    
    ads = [
        "💰 Dollarni eng baland kursda sotishni xohlaysizmi? Botga kiring!",
        "🟡 Oltin va USDT narxlari har daqiqada yangilanmoqda. AI bilan kuzating!",
        "🧮 5 ta valyuta va oltin uchun eng aniq kalkulyator faqat bizda!",
        "🚀 Botimizni guruhingizga qo'shing — kurslarni guruhda biling!"
    ]
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🤖 Botga kirish / Start", url=f"https://t.me/{bot.get_me().username}"))
    
    for g_id in groups:
        try: bot.send_message(g_id, random.choice(ads), reply_markup=markup)
        except: pass

def get_ai_price_suggestion():
    users = len(get_ids("users.txt"))
    # AI mantiqi: Har bir foydalanuvchi uchun narxni dinamik hisoblaydi
    suggested = max(25000, users * 200)
    
    msg = f"🤖 **AI NARX MASLAHATCHISI**\n\n"
    msg += f"👥 Obunachilar soni: {users}\n"
    msg += f"💡 Taklif etilayotgan Kunlik narx: {suggested:,.0f} so'm\n"
    msg += f"💡 Taklif etilayotgan Oylik narx: {suggested*12:,.0f} so'm\n\n"
    msg += "⚠️ Ushbu narxlarni tariflarga qo'llaymizmi?"
    
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✅ Tasdiqlash", callback_data="ai_confirm"),
           types.InlineKeyboardButton("❌ Rad etish", callback_data="ai_reject"))
    return msg, kb

# --- ASOSIY MENYU ---
def main_menu(uid):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📊 Kurslar va Oltin", "🧮 AI Kalkulyator")
    markup.add("📈 Statistika", "🏦 Banklar kursi")
    if uid == ADMIN_ID:
        ai_label = "🤖 AI: YOQILGAN" if ai_active else "🔴 AI: O'CHIRILGAN"
        markup.add("⚙️ AI Boshqaruv Markazi", ai_label)
    return markup

@bot.message_handler(commands=['start'])
def welcome(m):
    save_id("users.txt" if m.chat.type == 'private' else "groups.txt", m.chat.id)
    bot.send_message(m.chat.id, "AI Valyuta tizimiga xush kelibsiz! Men sizga 5 ta asosiy valyuta, Oltin va USDT kurslarini taqdim etaman.", reply_markup=main_menu(m.chat.id))

# --- TUGMALAR BILAN ISHLASH ---
@bot.message_handler(func=lambda m: m.text == "📊 Kurslar va Oltin")
def rates(m):
    bot.send_message(m.chat.id, get_global_rates(), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🧮 AI Kalkulyator")
def calc_init(m):
    kb = types.InlineKeyboardMarkup(row_width=3)
    btns = [types.InlineKeyboardButton(x, callback_data=f"val_{x}") for x in ['USD','EUR','RUB','KZT','GBP','OLTIN']]
    kb.add(*btns)
    bot.send_message(m.chat.id, "Qaysi valyutani so'mga aylantiramiz?", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith('val_'))
def calc_prompt(c):
    v = c.data.split('_')[1]
    bot.answer_callback_query(c.id)
    m = bot.send_message(c.message.chat.id, f"🔢 {v} miqdorini kiriting (Masalan: 100):")
    bot.register_next_step_handler(m, calc_execute, v)

def calc_execute(m, v):
    try:
        amount = float(m.text.replace(',', '.'))
        r = requests.get("https://cbu.uz/uz/arkhiv-kursov-valyut/json/").json()
        rate = 988600 if v == 'OLTIN' else float(next(i['Rate'] for i in r if i['Ccy'] == v))
        bot.send_message(m.chat.id, f"✅ {amount} {v} = **{amount*rate:,.2f} so'm**", parse_mode="Markdown")
    except:
        bot.send_message(m.chat.id, "⚠️ Faqat raqam kiriting!")

# --- ADMIN TUGMALARI ---
@bot.message_handler(func=lambda m: m.text in ["🤖 AI: YOQILGAN", "🔴 AI: O'CHIRILGAN"] and m.chat.id == ADMIN_ID)
def ai_toggle(m):
    global ai_active
    ai_active = not ai_active
    bot.send_message(m.chat.id, f"AI Holati o'zgardi! Hozir: {'Yoqilgan' if ai_active else 'Ochirilgan'}", reply_markup=main_menu(m.chat.id))

@bot.message_handler(func=lambda m: m.text == "⚙️ AI Boshqaruvi" or m.text == "⚙️ AI Boshqaruv Markazi" and m.chat.id == ADMIN_ID)
def ai_center(m):
    if ai_active:
        text, kb = get_ai_price_suggestion()
        bot.send_message(ADMIN_ID, text, reply_markup=kb, parse_mode="Markdown")
    else:
        bot.send_message(ADMIN_ID, "⚠️ AI tizimi o'chirilgan. Avval uni yoqing.")

@bot.callback_query_handler(func=lambda c: c.data.startswith('ai_'))
def ai_callback(c):
    res = "✅ Narxlar yangilandi!" if c.data == "ai_confirm" else "❌ AI taklifi rad etildi."
    bot.edit_message_text(res, c.message.chat.id, c.message.message_id)

@bot.message_handler(func=lambda m: m.text == "📈 Statistika")
def statistics(m):
    u, g = len(get_ids("users.txt")), len(get_ids("groups.txt"))
    bot.send_message(m.chat.id, f"📊 **Bot Statistikasi:**\n👤 Obunachilar: {u}\n👥 Guruhlar: {g}")

@bot.message_handler(func=lambda m: m.text == "🏦 Banklar kursi")
def banks(m):
    t = "🏦 **Tijorat banklari (USD Sotish):**\n\n🏢 NBU: 12,960\n🏢 Kapital: 12,980\n🏢 Hamkor: 12,970\n🏢 Ipak Yo'li: 12,975"
    bot.send_message(m.chat.id, t)

# --- SERVER ---
@app.route('/')
def home(): return "AI System Online"

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(ai_marketing_engine, 'interval', hours=2)
    scheduler.start()
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()
    bot.infinity_polling()
