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

# AI Holati (Boshlang'ich holatda yoqilgan)
ai_status = True 

# --- BAZA ---
def get_list(f):
    try:
        with open(f, "r") as file: return file.read().splitlines()
    except: return []

def save_id(f, id):
    ids = get_list(f)
    if str(id) not in ids:
        with open(f, "a") as file: file.write(str(id) + "\n")

# --- AI REKLAMA (FAQAT AI YOQILGAN BO'LSA ISHLAYDI) ---
def ai_marketing_job():
    global ai_status
    if not ai_status: return # Agar AI o'chiq bo'lsa, reklama ketmaydi
    
    groups = get_list("groups.txt")
    if not groups: return
    
    ai_texts = [
        "🎁 Botimizga kirib 'Start' bosing va yutuqli kurs tahlillarini oling!",
        "🟡 Oltin narxi o'zgarmoqda! AI bashoratlarini bot ichida ko'ring.",
        "📊 Valyuta hisoblashda adashmang, eng aqlli kalkulyator bizda!",
        "🚀 Guruhda kurslarni bilish uchun 'dollar' deb yozing yoki botga kiring."
    ]
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🚀 Botni ochish", url=f"https://t.me/{bot.get_me().username}"))
    
    for g_id in groups:
        try: bot.send_message(g_id, random.choice(ai_texts), reply_markup=markup)
        except: pass

# --- AI NARX MASLAHATI ---
def get_ai_suggestion():
    users = len(get_list("users.txt"))
    suggested_day = max(20000, users * 150)
    
    text = f"🤖 **AI NARX MASLAHATI**\n\n"
    text += f"👥 Obunachilar: {users} ta\n"
    text += f"💡 AI taklifi (Kunlik): {suggested_day:,.0f} so'm\n"
    text += f"💡 AI taklifi (Oylik): {suggested_day*12:,.0f} so'm\n\n"
    text += "✅ Ushbu narxlarni tasdiqlaysizmi?"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Tasdiqlash", callback_data="confirm_p"),
               types.InlineKeyboardButton("❌ Rad etish", callback_data="reject_p"))
    return text, markup

# --- ASOSIY MENYU ---
def main_kb(uid):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📊 Kurslar va Oltin", "🧮 AI Kalkulyator")
    markup.add("📈 Statistika", "🏦 Banklar kursi")
    if uid == ADMIN_ID:
        # AI holatiga qarab tugma nomi o'zgaradi
        status_text = "🤖 AI: YOQILGAN" if ai_status else "🔴 AI: O'CHIRILGAN"
        markup.add("⚙️ AI Boshqaruvi", status_text)
    return markup

@bot.message_handler(commands=['start'])
def start(m):
    save_id("users.txt" if m.chat.type == 'private' else "groups.txt", m.chat.id)
    bot.send_message(m.chat.id, "AI Valyuta tizimi faoliyatini boshladi!", reply_markup=main_kb(m.chat.id))

# --- ADMIN: AI O'CHIRIB YOQISH ---
@bot.message_handler(func=lambda m: m.text in ["🤖 AI: YOQILGAN", "🔴 AI: O'CHIRILGAN"] and m.chat.id == ADMIN_ID)
def toggle_ai(m):
    global ai_status
    ai_status = not ai_status # Holatni almashtirish
    text = "✅ AI tizimi ishga tushirildi! Endi u guruhlarda reklama qiladi." if ai_status else "🛑 AI tizimi to'xtatildi. Guruhlarga reklama ketmaydi."
    bot.send_message(m.chat.id, text, reply_markup=main_kb(m.chat.id))

@bot.message_handler(func=lambda m: m.text == "⚙️ AI Boshqaruvi" and m.chat.id == ADMIN_ID)
def ai_manage(m):
    if ai_status:
        text, markup = get_ai_suggestion()
        bot.send_message(ADMIN_ID, text, reply_markup=markup, parse_mode="Markdown")
    else:
        bot.send_message(ADMIN_ID, "⚠️ AI hozirda o'chirilgan. Uni yoqish uchun pastdagi tugmani bosing.")

# --- KALKULYATOR ---
@bot.message_handler(func=lambda m: m.text == "🧮 AI Kalkulyator")
def calc_select(m):
    kb = types.InlineKeyboardMarkup(row_width=3)
    btns = [types.InlineKeyboardButton(x, callback_data=f"c_{x}") for x in ['USD','EUR','RUB','KZT','GBP','OLTIN']]
    kb.add(*btns)
    bot.send_message(m.chat.id, "Qaysi valyutani so'mga hisoblaymiz?", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith('c_'))
def calc_input(c):
    val = c.data.split('_')[1]
    msg = bot.send_message(c.message.chat.id, f"🔢 {val} miqdorini yozing:")
    bot.register_next_step_handler(msg, calc_res, val)

def calc_res(m, val):
    try:
        amt = float(m.text.replace(',', '.'))
        r = requests.get("https://cbu.uz/uz/arkhiv-kursov-valyut/json/").json()
        rate = 985450 if val == 'OLTIN' else float(next(i['Rate'] for i in r if i['Ccy'] == val))
        bot.send_message(m.chat.id, f"✅ {amt} {val} = **{amt*rate:,.2f} so'm**", parse_mode="Markdown")
    except: bot.send_message(m.chat.id, "⚠️ Faqat raqam yozing.")

# --- KURSLAR VA STATISTIKA ---
@bot.message_handler(func=lambda m: m.text == "📊 Kurslar va Oltin")
def show_r(m):
    try:
        r = requests.get("https://cbu.uz/uz/arkhiv-kursov-valyut/json/").json()
        usd = next(i['Rate'] for i in r if i['Ccy'] == 'USD')
        bot.send_message(m.chat.id, f"🟡 Oltin: 985,450 so'm\n🇺🇸 1 USD = {usd} so'm\n🇪🇺 1 EUR = {next(i['Rate'] for i in r if i['Ccy'] == 'EUR')} so'm")
    except: bot.send_message(m.chat.id, "Tizimda uzilish...")

@bot.message_handler(func=lambda m: m.text == "📈 Statistika")
def show_s(m):
    u, g = len(get_list("users.txt")), len(get_list("groups.txt"))
    bot.send_message(m.chat.id, f"📊 **Statistika:**\n👤 Obunachilar: {u}\n👥 Guruhlar: {g}")

# --- SERVER ---
@app.route('/')
def h(): return "AI System Running"

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(ai_marketing_job, 'interval', hours=2)
    scheduler.start()
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()
    bot.infinity_polling()
