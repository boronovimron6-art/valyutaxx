import telebot
import requests
import random
import json
import os
from telebot import types
from flask import Flask
from threading import Thread
from apscheduler.schedulers.background import BackgroundScheduler

# --- SOZLAMALAR ---
TOKEN = '8606825506:AAHoLYaanIjoudJ5zDuhWsFkK-VG_FV29nk'
ADMIN_ID = 505222809 
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Yashirin sozlamalar
referral_reward = 500  # Har bir yashirin taklif uchun (so'm)
TARGET_LIMIT = 5000    # Reklama menejeri faollashish chegarasi

# --- BAZA BILAN ISHLASH ---
def load_db():
    if os.path.exists("db.json"):
        with open("db.json", "r") as f: return json.load(f)
    return {"users": {}, "daily_stats": {"new_refs": 0, "total_payout": 0}}

def save_db(data):
    with open("db.json", "w") as f: json.dump(data, f)

# --- AI MENEJER: REKLAMA QIDIRISH (FAQAT ADMINGA) ---
def ai_business_manager():
    db = load_db()
    total_users = len(db["users"])
    
    if total_users >= TARGET_LIMIT:
        report = "🚀 **AI MENEJER: REKLAMA QIDIRISH REJIMI**\n"
        report += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        report += f"📊 Auditoriya: {total_users} ta faol foydalanuvchi.\n"
        report += "🎯 **Tavsiya etilgan sohalar:**\n"
        report += "• Maishiy texnika (Artel, Samsung)\n• Onlayn do'konlar (Uzun, Zoodmall)\n• O'quv markazlari\n\n"
        report += "🚫 **FILTR:** Qimor (1xbet) va pornografik reklamalar bloklangan.\n"
        report += "⚠️ **ESLATMA:** Reklama joylashtirish tugmasi faqat sizda mavjud."
        bot.send_message(ADMIN_ID, report, parse_mode="Markdown")
    else:
        bot.send_message(ADMIN_ID, f"📈 **AI:** 5000 taga yetishimizga {TARGET_LIMIT - total_users} ta odam qoldi.")

# --- ASOSIY MENYU ---
def main_menu(uid):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📊 Kurslar va Oltin", "🧮 AI Kalkulyator")
    markup.add("🏦 Banklar kursi", "📈 Statistika")
    if uid == ADMIN_ID:
        markup.add("🤖 AI Yashirin Hisoboti", "📢 Reklama Joylash")
        markup.add("🎁 Mukofot Sozlamasi", "⚙️ Tariflar")
    return markup

@bot.message_handler(commands=['start'])
def start(m):
    db = load_db()
    uid = str(m.chat.id)
    
    if uid not in db["users"]:
        args = m.text.split()
        referrer = args[1] if len(args) > 1 else None
        db["users"][uid] = {"balance": 0, "ref_count": 0, "invited_by": referrer}
        
        if referrer and referrer in db["users"] and referrer != uid:
            db["users"][referrer]["balance"] += referral_reward
            db["users"][referrer]["ref_count"] += 1
            db["daily_stats"]["new_refs"] += 1
            db["daily_stats"]["total_payout"] += referral_reward
            
    save_db(db)
    bot.send_message(m.chat.id, "Valyuta botiga xush kelibsiz!", reply_markup=main_menu(m.chat.id))

# --- ADMIN: REKLAMA JOYLASHTIRISH ---
@bot.message_handler(func=lambda m: m.text == "📢 Reklama Joylash" and m.chat.id == ADMIN_ID)
def ask_ad(m):
    msg = bot.send_message(ADMIN_ID, "Reklama xabarini (rasm, matn yoki video) yuboring. Men uni hamma foydalanuvchilarga tarqataman:")
    bot.register_next_step_handler(msg, broadcast_ad)

def broadcast_ad(m):
    db = load_db()
    count = 0
    for user_id in db["users"]:
        try:
            bot.copy_message(user_id, m.chat.id, m.message_id)
            count += 1
        except: pass
    bot.send_message(ADMIN_ID, f"✅ Reklama {count} ta foydalanuvchiga muvaffaqiyatli yuborildi!")

# --- ADMIN: YASHIRIN HISOBOT ---
@bot.message_handler(func=lambda m: m.text == "🤖 AI Yashirin Hisoboti" and m.chat.id == ADMIN_ID)
def secret_report(m):
    db = load_db()
    top_ref = sorted(db["users"].items(), key=lambda x: x[1].get('ref_count',0), reverse=True)[:5]
    
    report = "🕵️ **AI YASHIRIN HISOBOTI**\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    report += f"📈 Bugungi o'sish: {db['daily_stats']['new_refs']} ta\n"
    report += f"💰 To'lanishi kerak: {db['daily_stats']['total_payout']:,} so'm\n\n"
    report += "🏆 **TOP REKLAMACHILAR:**\n"
    for i, (uid, data) in enumerate(top_ref, 1):
        if data.get('ref_count', 0) > 0:
            report += f"{i}. ID: `{uid}` — {data['ref_count']} ta (Balans: {data['balance']:,} so'm)\n"
    
    bot.send_message(ADMIN_ID, report, parse_mode="Markdown")
    ai_business_manager() # Reklama menejeri hisobotini ham qo'shib yuboradi

# --- VALYUTA VA KALKULYATOR ---
@bot.message_handler(func=lambda m: m.text == "📊 Kurslar va Oltin")
def send_rates(m):
    r = requests.get("https://cbu.uz/uz/arkhiv-kursov-valyut/json/").json()
    targets = {'USD':'🇺🇸','EUR':'🇪🇺','RUB':'🇷🇺','KZT':'🇰🇿','GBP':'🇬🇧'}
    text = "🟡 **OLTIN (1 gr): 995,000 so'm**\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    for c, e in targets.items():
        rate = next(i['Rate'] for i in r if i['Ccy'] == c)
        text += f"{e} 1 {c} = {rate} so'm\n"
    bot.send_message(m.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🧮 AI Kalkulyator")
def start_calc(m):
    kb = types.InlineKeyboardMarkup(row_width=3)
    btns = [types.InlineKeyboardButton(x, callback_data=f"c_{x}") for x in ['USD','EUR','RUB','KZT','GBP','OLTIN']]
    kb.add(*btns)
    bot.send_message(m.chat.id, "Valyutani tanlang:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith('c_'))
def calc_step(c):
    v = c.data.split('_')[1]
    msg = bot.send_message(c.message.chat.id, f"🔢 {v} miqdorini yozing:")
    bot.register_next_step_handler(msg, calc_finish, v)

def calc_finish(m, v):
    try:
        amt = float(m.text.replace(',', '.'))
        r = requests.get("https://cbu.uz/uz/arkhiv-kursov-valyut/json/").json()
        rate = 995000 if v == 'OLTIN' else float(next(i['Rate'] for i in r if i['Ccy'] == v))
        bot.send_message(m.chat.id, f"✅ {amt} {v} = **{amt*rate:,.2f} so'm**", parse_mode="Markdown")
    except: bot.send_message(m.chat.id, "Faqat raqam yozing!")

# --- SERVER ---
@app.route('/')
def h(): return "Bot Online"

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(ai_business_manager, 'cron', hour=22, minute=0)
    scheduler.start()
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()
    bot.infinity_polling()
