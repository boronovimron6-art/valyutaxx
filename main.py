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
scheduler = BackgroundScheduler()
scheduler.start()

# --- BAZA BILAN ISHLASH ---
def get_list(file_name):
    try:
        with open(file_name, "r") as f: return f.read().splitlines()
    except: return []

def save_id(file_name, target_id):
    ids = get_list(file_name)
    if str(target_id) not in ids:
        with open(file_name, "a") as f: f.write(str(target_id) + "\n")

# --- AI: TARIFLAR VA AVTO-NARX ---
def get_ai_pricing():
    user_count = len(get_list("users.txt"))
    base = max(user_count * 75, 15000) # AI narxni biroz oshirdi (sifat evaziga)
    
    tariffs = {
        "Kunlik": base, "Haftalik": base * 4, "Oylik": base * 12,
        "Kvartal": base * 30, "Yarim yillik": base * 55, "Yillik": base * 100
    }
    
    text = f"🤖 **AI REKLAMA TARIFLARI**\n👥 Foydalanuvchilar: {user_count}\n\n"
    for p, pr in tariffs.items():
        text += f"📅 {p}: {pr:,.0f} so'm\n"
    text += "\n⚠️ *Narxlar AI tomonidan auditoriya qamroviga qarab belgilandi.*"
    return text

# --- MA'LUMOTLARNI OLISH (API) ---
def get_combined_data():
    try:
        # MB kurslari
        r = requests.get("https://cbu.uz/uz/arkhiv-kursov-valyut/json/").json()
        gold = next(i['Rate'] for i in r if i['Ccy'] == 'XAU') or "680,000"
        
        # Kripto (USDT) - Taxminiy bozor kursi
        usdt = 12980 
        
        currencies = ['USD', 'EUR', 'RUB', 'KZT', 'GBP']
        res = f"🟡 **OLTIN (1 gr): {gold} so'm**\n"
        res += f"💎 **USDT (Kripto): {usdt:,.0f} so'm**\n"
        res += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        
        for c in currencies:
            curr = next(i for i in r if i['Ccy'] == c)
            icon = {'USD':'🇺🇸','EUR':'🇪🇺','RUB':'🇷🇺','KZT':'🇰🇿','GBP':'🇬🇧'}[c]
            res += f"{icon} 1 {c} = {curr['Rate']} so'm\n"
        
        res += f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n📅 {r[0]['Date']}"
        return res
    except: return "⚠️ Ma'lumot yangilanishida xatolik."

# --- AI AVTO-MARKETING ---
def ai_auto_marketing():
    groups = get_list("groups.txt")
    if not groups: return
    texts = [
        "💰 Dollarni eng foydali kursda almashtirmoqchimisiz? Botga kiring!",
        "🟡 Oltin va Kumush narxlari har 5 daqiqada yangilanmoqda!",
        "📊 Banklardagi navbatlardan charchadingizmi? Kurslarni botda tekshiring!",
        "🚀 AI yordamida valyuta hisoblash endi juda oson!"
    ]
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🤖 Botni ishga tushirish", url=f"https://t.me/{bot.get_me().username}"))
    for g in groups:
        try: bot.send_message(g, random.choice(texts), reply_markup=markup)
        except: pass

# --- ASOSIY MENYU ---
def main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📊 Kurslar va Oltin", "🧮 AI Kalkulyator")
    markup.add("🏦 Banklar kursi", "📈 Statistika")
    if str(user_id) == str(ADMIN_ID):
        markup.add("🤖 AI Reklama Paneli")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    save_id("users.txt" if message.chat.type == 'private' else "groups.txt", message.chat.id)
    bot.send_message(message.chat.id, "Siz bilan AI Valyuta Assistenti. Xizmatga tayyorman!", reply_markup=main_menu(message.chat.id))

# --- KALKULYATOR (5 VALYUTA + OLTIN) ---
@bot.message_handler(func=lambda m: m.text == "🧮 AI Kalkulyator")
def calc_start(m):
    markup = types.InlineKeyboardMarkup(row_width=3)
    btns = [types.InlineKeyboardButton(x, callback_data=f"cl_{x}") for x in ['USD','EUR','RUB','KZT','GBP','OLTIN']]
    markup.add(*btns)
    bot.send_message(m.chat.id, "Hisoblamoqchi bo'lgan valyutangizni tanlang:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith('cl_'))
def calc_callback(c):
    val = c.data.split('_')[1]
    msg = bot.send_message(c.message.chat.id, f"🔢 {val} miqdorini kiriting:")
    bot.register_next_step_handler(msg, process_calculation, val)

def process_calculation(m, val):
    try:
        amt = float(m.text)
        r = requests.get("https://cbu.uz/uz/arkhiv-kursov-valyut/json/").json()
        rate = float(next(i['Rate'] for i in r if (i['Ccy'] == val or (val == 'OLTIN' and i['Ccy'] == 'XAU'))))
        bot.send_message(m.chat.id, f"✅ {amt} {val} = **{amt*rate:,.2f} so'm**", parse_mode="Markdown")
    except: bot.send_message(m.chat.id, "⚠️ Faqat raqam kiriting!")

# --- BOSHQA FUNKSIYALAR ---
@bot.message_handler(func=lambda m: m.text == "📊 Kurslar va Oltin")
def rates(m): bot.send_message(m.chat.id, get_combined_data(), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🤖 AI Reklama Paneli" and m.chat.id == ADMIN_ID)
def admin_p(m): bot.send_message(ADMIN_ID, get_ai_pricing(), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📈 Statistika")
def stats(m):
    u, g = len(get_list("users.txt")), len(get_list("groups.txt"))
    bot.send_message(m.chat.id, f"📊 **Bot holati:**\n👤 Obunachilar: {u}\n👥 Guruhlar: {g}")

# --- SERVER ---
@app.route('/')
def h(): return "AI System Online"

if __name__ == "__main__":
    scheduler.add_job(ai_auto_marketing, 'interval', hours=2)
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()
    bot.infinity_polling()
