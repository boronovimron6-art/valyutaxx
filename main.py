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
                if "config" not in db:
                    db["config"] = {"reward": 500}
                return db
            except: return {"users": {}, "groups": {}, "ads": [], "config": {"reward": 500}}
    return {"users": {}, "groups": {}, "ads": [], "config": {"reward": 500}}

def save_db(data):
    with open("ai_master_db.json", "w") as f:
        json.dump(data, f, indent=4)

# --- VALYUTA FUNKSIYALARI ---
def get_cbu_rates(mode="main"):
    try:
        r = requests.get("https://cbu.uz/uz/arkhiv-kursov-valyut/json/").json()
        if mode == "main":
            main_list = {'USD':'🇺🇸','EUR':'🇪🇺','RUB':'🇷🇺','KZT':'🇰🇿','GBP':'🇬🇧'}
            text = "🏛 **Manba: Markaziy Bank**\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            for c, e in main_list.items():
                rate = next(i['Rate'] for i in r if i['Ccy'] == c)
                text += f"{e} 1 {c} = {rate} so'm\n"
            return text
        else:
            text = "🌐 **Boshqa Valyutalar:**\n"
            for i in r[5:25]:
                text += f"🔹 1 {i['Ccy']} = {i['Rate']} so'm\n"
            return text
    except: return "⚠️ Kurslarni olishda xatolik."

# --- ASOSIY MENYU ---
def main_menu(uid):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📊 Asosiy Kurslar", "🌐 Boshqa Kurslar")
    markup.add("🏦 Banklar Kursi", "💰 Eng yaxshi kurs")
    markup.add("📍 Yaqin banklar", "✍️ Adminga murojaat")
    
    if uid == ADMIN_ID:
        markup.add("📈 Statistika", "📑 Kunlik Kotib Hisoboti")
        markup.add("💡 AI Biznes Maslahati", "📢 Reklama Joylash")
        markup.add("⚙️ Mukofotni Sozlash")
    else:
        markup.add("💬 AI bilan suhbat")
    return markup

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
    bot.send_message(m.chat.id, "🤖 Salom! Men aqlli bank kotibingizman.", reply_markup=main_menu(m.chat.id))

# --- ADMINGA XABAR QOLDIRISH ---
@bot.message_handler(func=lambda m: m.text == "✍️ Adminga muro
