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
        with open("db.json", "r") as f: 
            try: return json.load(f)
            except: return {"users": {}, "daily_stats": {"new_refs": 0, "total_payout": 0}}
    return {"users": {}, "daily_stats": {"new_refs": 0, "total_payout": 0}}

def save_db(data):
    with open("db.json", "w") as f: 
        json.dump(data, f, indent=4)

# --- AI MENEJER: REKLAMA QIDIRISH (FAQAT ADMINGA) ---
def ai_business_manager():
    db = load_db()
    total_users = len(db["users"])
    
    if total_users >= TARGET_LIMIT:
        report = "🚀 **AI MENEJER: REKLAMA QIDIRISH REJIMI**\n"
        report += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        report += f"📊 Auditoriya: {total_users} ta faol foydalanuvchi.\n"
        report += "🎯 **Tavsiya etilgan sohalar:**\n"
        report += "• Maishiy texnika, Onlayn do'konlar, O'quv markazlari.\n\n"
        report += "🚫 **FILTR:** Qimor (1xbet) va odobsiz reklamalar bloklangan.\n"
        report += "⚠️ **ESLATMA:** Reklama joylashtirish huquqi faqat sizda."
        bot.send_message(ADMIN_ID, report, parse_mode="Markdown")
    else:
        # 5000 gacha yetish uchun motivatsiya (faqat adminga)
        pass

# --- ASOSIY MENYU ---
def main_menu(uid):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📊 Kurslar va Oltin", "🧮 AI Kalkulyator")
    markup.add("🏦 Banklar kursi", "📈 Statistika")
    if uid == ADMIN_ID:
        markup.add("🕵️ AI Yashirin Hisoboti", "📢 Reklama Joylash")
        markup.add("🎁 Mukofotni Sozlash", "⚙️ Boshqaruv")
    return markup

@bot.message_handler(commands=['start'])
def start(m):
    db = load_db()
    uid = str(m.chat.id)
    
    if uid not in db["users"]:
        # Yashirin referal linkni tekshirish
        args = m.text.split()
        referrer = args[1] if len(args) > 1 else None
        
        db["users"][uid] = {"balance": 0, "ref_count": 0, "
