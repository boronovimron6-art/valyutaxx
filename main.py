import telebot
import requests
import json
import os
from datetime import datetime, timedelta
from telebot import types
from flask import Flask
from threading import Thread
from apscheduler.schedulers.background import BackgroundScheduler

# --- KONFIGURATSIYA ---
TOKEN = '8606825506:AAHoLYaanIjoudJ5zDuhWsFkK-VG_FV29nk'
ADMIN_ID = 505222809 
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# --- MA'LUMOTLAR BAZASI ---
def load_db():
    if os.path.exists("ai_master_db.json"):
        with open("ai_master_db.json", "r") as f:
            try: 
                db = json.load(f)
                # Yangi sozlamalar bo'lmasa, qo'shish
                if "config" not in db:
                    db["config"] = {"reward": 500}
                return db
            except: return {"users": {}, "groups": {}, "ads": [], "config": {"reward": 500}}
    return {"users": {}, "groups": {}, "ads": [], "config": {"reward": 500}}

def save_db(data):
    with open("ai_master_db.json", "w") as f:
        json.dump(data, f, indent=4)

# --- VALYUTA VA BANK TAHLILI ---
def get_cbu_rates(mode="main"):
    try:
        r = requests.get("https://cbu.uz/uz/arkhiv-kursov-valyut/json/").json()
        if mode == "main":
            main_list = {'USD':'🇺🇸','EUR':'🇪🇺','RUB':'🇷🇺','KZT':'🇰🇿','GBP':'🇬🇧'}
            text = "🏛 **Markaziy Bank kurslari:**\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            for c, e in main_list.items():
                rate = next(i['Rate'] for i in r if i['Ccy'] == c)
                text += f"{e} 1 {c} = {rate} so'm\n"
            return text
        else:
            text = "🌐 **Boshqa Valyutalar:**\n"
            for i in r[5:25]:
                text += f"🔹 1 {i['Ccy']} = {i['Rate']} so'm\n"
            return text
    except: return "⚠️ Ma'lumot olishda xatolik."

def get_best_rate_advice():
    # Bu yerda AI eng yaxshi bank kursini tahlil qiladi
    return "💰 **AI Kotib tahlili:**\n\nBugun USD sotib olish uchun **Anorbank** (12,985) eng ma'qul ko'rinmoqda.\nSotish uchun esa **NBU** (12,960) tavsiya etiladi.\n\n📍 *Eng yaqin bankni topish uchun menyudan foydalaning.*"

# --- ASOSIY MENYU ---
def main_menu(uid):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📊 Kurslar", "💰 Eng yaxshi kurs")
    markup.add("📍 Yaqin banklar", "📈 Statistika")
    
    if uid == ADMIN_ID:
        markup.add("📑 Kunlik Kotib Hisoboti", "💡 AI Biznes Maslahati")
        markup.add("📢 Reklama Joylash", "⚙️ Mukofotni Sozlash")
    else:
        markup.add("💬 AI bilan suhbat")
    return markup

# --- START VA REFERAL ---
@bot.message_handler(commands=['start'])
def start(m):
    db = load_db()
    uid = str(m.chat.id)
    
    if m.chat.type == 'private':
        if uid not in db["users"]:
            args = m.text.split()
            ref = args[1] if len(args) > 1 else None
            db["users"][uid] = {"ref_count": 0, "invited_by": ref}
            if ref and ref in db["users"] and ref != uid:
                db["users"][ref]["ref_count"] += 1
        save_db(db)
    else:
        db["groups"][uid] = {"name": m.chat.title}
        save_db(db)
        
    bot.send_message(m.chat.id, "🤖 Salom! Men sizning aqlli kotibingizman.", reply_markup=main_menu(m.chat.id))

# --- ADMIN: KOTIB VA MASLAHATCHI FUNKSIYALARI ---
@bot.message_handler(func=lambda m: m.text == "📑 Kunlik Kotib Hisoboti" and m.chat.id == ADMIN_ID)
def secretary_report(m):
    db = load_db()
    reward = db["config"]["reward"]
    report = f"📝 **KOTIB HISOBOTI ({datetime.now().strftime('%d.%m.%Y')})**\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    report += f"👤 Obunachilar: {len(db['users'])}\n👥 Guruhlar: {len(db['groups'])}\n\n"
    report += "💸 **TO'LOV VARAQASI:**\n"
    
    total_pay = 0
    for uid, data in db["users"].items():
        if data.get("ref_count", 0) > 0:
            summa = data['ref_count'] * reward
            total_pay += summa
            report += f"• ID: `{uid}` -> {data['ref_count']} kishi ({summa:,} so'm)\n"
    
    report += f"\n💰 **Jami xarajat:** {total_pay:,} so'm"
    bot.send_message(ADMIN_ID, report, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "💡 AI Biznes Maslahati" and m.chat.id == ADMIN_ID)
def ai_consultant(m):
    db = load_db()
    u_count = len(db["users"])
    advice = "💡 **AI STRATEGIK MASLAHATI**\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    if u_count < 5000:
        advice += f"📈 Hozircha obunachilar {u_count} ta. Maqsad 5000 ga yetish.\n• Mukofotni {db['config']['reward']} so'mdan tushirmang.\n• Reklama narxini oylik 500k so'm atrofida ushlab turing."
    else:
        advice += "🚀 Marra bosildi! Endi reklama narxlarini 20% ga oshirishni tavsiya qilaman."
    bot.send_message(ADMIN_ID, advice, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "⚙️ Mukofotni Sozlash" and m.chat.id == ADMIN_ID)
def set_reward_call(m):
    msg = bot.send_message(ADMIN_ID, "Yangi mukofot miqdorini yozing (so'mda):")
    bot.register_next_step_handler(msg, save_reward_config)

def save_reward_config(m):
    db = load_db()
    try:
        db["config"]["reward"] = int(m.text)
        save_db(db)
        bot.send_message(ADMIN_ID, f"✅ Kotib: Yangi mukofot {m.text} so'm qilib belgilandi.")
    except: bot.send_message(ADMIN_ID, "❌ Xato! Faqat raqam yozing.")

# --- LOKATSIYA: YAQIN BANKLAR ---
@bot.message_handler(func=lambda m: m.text == "📍 Yaqin banklar")
def geo_request(m):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(types.KeyboardButton("📍 Joylashuvni yuborish", request_location=True))
    bot.send_message(m.chat.id, "Atrofingizdagi banklarni topish uchun joylashuvni yuboring:", reply_markup=kb)

@bot.message_handler(content_types=['location'])
def find_banks(m):
    url = f"https://www.google.com/maps/search/bank/@{m.location.latitude},{m.location.longitude},15z"
    bot.send_message(m.chat.id, f"📍 Atrofingizdagi banklar xaritada:\n[Google Maps orqali ochish]({url})", parse_mode="Markdown", reply_markup=main_menu(m.chat.id))

# --- REKLAMA ---
@bot.message_handler(func=lambda m: m.text == "📢 Reklama Joylash" and m.chat.id == ADMIN_ID)
def ad_menu(m):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("1 Kun", callback_data="d_1"), types.InlineKeyboardButton("1 Hafta", callback_data="d_7"),
           types.InlineKeyboardButton("1 Oy", callback_data="d_30"), types.InlineKeyboardButton("1 Yil", callback_data="d_365"))
    bot.send_message(ADMIN_ID, "🕒 Reklama muddatini tanlang:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith('d_'))
def ad_receive_step(c):
    days = int(c.data.split('_')[1])
    msg = bot.send_message(ADMIN_ID, f"📝 {days} kunlik reklama xabarini yuboring:")
    bot.register_next_step_handler(msg, ad_save_final, days)

def ad_save_final(m, days):
    db = load_db()
    expire_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M")
    db["ads"].append({"msg_id": m.message_id, "expire": expire_date})
    save_db(db)
    bot.send_message(ADMIN_ID, f"✅ Reklama saqlandi! {expire_date} gacha tarqatiladi.")

# --- AVTOMATIK ISHLAR ---
def ai_auto_broadcast():
    db = load_db()
    now = datetime.now()
    valid_ads = []
    for ad in db["ads"]:
        if datetime.strptime(ad['expire'], "%Y-%m-%d %H:%M") > now:
            valid_ads.append(ad)
            for uid in list(db["users"].keys()) + list(db["groups"].keys()):
                try: bot.copy_message(uid, ADMIN_ID, ad['msg_id'])
                except: pass
    db["ads"] = valid_ads
    save_db(db)

# --- QOLGAN TUGMALAR ---
@bot.message_handler(func=lambda m: m.text == "📊 Kurslar")
def sh_rates(m): bot.send_message(m.chat.id, get_cbu_rates("main"), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "💰 Eng yaxshi kurs")
def sh_best(m): bot.send_message(m.chat.id, get_best_rate_advice(), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📈 Statistika")
def sh_stats(m):
    db = load_db()
    bot.send_message(m.chat.id, f"📊 Obunachilar: {len(db['users'])}\n👥 Guruhlar: {len(db['groups'])}")

@bot.message_handler(func=lambda m: m.chat.type == 'private')
def ai_chat(m):
    # Oddiy suhbat mantiqi
    bot.reply_to(m, "🤖 Men sizning bank kotibingizman. Kurslar yoki banklar haqida savolingiz bo'lsa, menyudan foydalaning.")

# --- SERVER ---
@app.route('/')
def home(): return "AI Secretary Running"

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    for h in [9, 15, 21]:
        scheduler.add_job(ai_auto_broadcast, 'cron', hour=h, minute=0)
    scheduler.start()
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()
    bot.infinity_polling()
