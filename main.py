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
    if not os.path.exists("ai_master_db.json"):
        return {"users": {}, "groups": {}, "ads": [], "config": {"reward": 500}}
    with open("ai_master_db.json", "r") as f:
        try:
            db = json.load(f)
            if "config" not in db: db["config"] = {"reward": 500}
            return db
        except:
            return {"users": {}, "groups": {}, "ads": [], "config": {"reward": 500}}

def save_db(data):
    with open("ai_master_db.json", "w") as f:
        json.dump(data, f, indent=4)

# --- VALYUTA FUNKSIYASI ---
def get_cbu_rates(mode="main"):
    try:
        r = requests.get("https://cbu.uz/uz/arkhiv-kursov-valyut/json/", timeout=10).json()
        if mode == "main":
            main_list = {'USD':'🇺🇸','EUR':'🇪🇺','RUB':'🇷🇺','KZT':'🇰🇿','GBP':'🇬🇧'}
            text = f"🏛 **KUNLIK VALYUTA KURSI**\n📅 {datetime.now().strftime('%d.%m.%Y')}\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            for c, e in main_list.items():
                rate = next(i['Rate'] for i in r if i['Ccy'] == c)
                text += f"{e} 1 {c} = {rate} so'm\n"
            text += "\n🏦 Manba: Markaziy Bank"
            return text
        else:
            text = "🌐 **BOSHQA VALYUTALAR**\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            for i in r[5:25]:
                text += f"🔹 1 {i['Ccy']} = {i['Rate']} so'm\n"
            return text
    except:
        return "⚠️ Kurslarni yuklashda xatolik yuz berdi."

# --- AVTOMATIK VAZIFALAR ---
def auto_currency_update():
    db = load_db()
    text = "📢 **XAYRLI TONG! BUGUNGI KURSLAR:**\n\n" + get_cbu_rates("main")
    all_targets = list(db["users"].keys()) + list(db["groups"].keys())
    for target in all_targets:
        try: bot.send_message(target, text, parse_mode="Markdown")
        except: continue

def auto_broadcast():
    db = load_db()
    now = datetime.now()
    active_ads = []
    for ad in db["ads"]:
        try:
            expire_at = datetime.strptime(ad['expire'], "%Y-%m-%d %H:%M")
            if expire_at > now:
                active_ads.append(ad)
                all_targets = list(db["users"].keys()) + list(db["groups"].keys())
                for target in all_targets:
                    try: bot.copy_message(target, ADMIN_ID, ad['msg_id'])
                    except: continue
        except: continue
    db["ads"] = active_ads
    save_db(db)

# --- MENYU ---
def main_menu(uid):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📊 Asosiy Kurslar", "🌐 Boshqa Kurslar")
    markup.add("🏦 Banklar Kursi", "💰 Eng yaxshi kurs")
    markup.add("📍 Yaqin banklar", "✍️ Adminga murojaat")
    if uid == ADMIN_ID:
        markup.add("📈 Statistika", "📑 Kunlik Kotib Hisoboti")
        markup.add("📢 Reklama Joylash", "⚙️ Mukofotni Sozlash")
    else:
        markup.add("💬 AI bilan suhbat")
    return markup

# --- HANDLERLAR ---
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
    bot.send_message(m.chat.id, "🤖 Salom! Men aqlli moliyaviy kotibman.", reply_markup=main_menu(m.chat.id))

@bot.message_handler(func=lambda m: m.text == "✍️ Adminga murojaat")
def contact_admin(m):
    msg = bot.send_message(m.chat.id, "📝 Admin uchun xabaringizni yozing:")
    bot.register_next_step_handler(msg, forward_to_admin)

def forward_to_admin(m):
    bot.send_message(ADMIN_ID, f"📩 **MUROJAAT:**\n👤 {m.from_user.first_name}\n🆔 `{m.chat.id}`\n💬 {m.text}")
    bot.send_message(m.chat.id, "✅ Adminga yetkazildi.", reply_markup=main_menu(m.chat.id))

@bot.message_handler(func=lambda m: m.text == "📈 Statistika" and m.chat.id == ADMIN_ID)
def admin_stats(m):
    db = load_db()
    bot.send_message(ADMIN_ID, f"📊 **STATISTIKA:**\n👤 Obunachilar: {len(db['users'])}\n👥 Guruhlar: {len(db['groups'])}")

@bot.message_handler(func=lambda m: m.text == "📊 Asosiy Kurslar")
def sh_main(m): bot.send_message(m.chat.id, get_cbu_rates("main"), parse_mode="Markdown")

@bot.message_handler(content_types=['location'])
def geo_map(m):
    url = f"https://www.google.com/maps/search/bank/@{m.location.latitude},{m.location.longitude},15z"
    bot.send_message(m.chat.id, f"📍 [Atrofingizdagi banklar]({url})", parse_mode="Markdown")

# --- SERVER VA ISHGA TUSHIRISH ---
@app.route('/')
def home(): return "Bot is running..."

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(auto_currency_update, 'cron', hour=9, minute=0)
    for h in [10, 16, 21]:
        scheduler.add_job(auto_broadcast, 'cron', hour=h, minute=0)
    scheduler.start()
    
    Thread(target=run_bot).start()
    app.run(host='0.0.0.0', port=10000)
