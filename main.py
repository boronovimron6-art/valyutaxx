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

# --- VALYUTA FUNKSIYALARI (CBU) ---
def get_cbu_rates(mode="main"):
    try:
        r = requests.get("https://cbu.uz/uz/arkhiv-kursov-valyut/json/").json()
        if mode == "main":
            main_list = {'USD':'🇺🇸','EUR':'🇪🇺','RUB':'🇷🇺','KZT':'🇰🇿','GBP':'🇬🇧'}
            text = "🏛 **Manba: O'zbekiston Markaziy Banki**\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            for c, e in main_list.items():
                rate = next(i['Rate'] for i in r if i['Ccy'] == c)
                text += f"{e} 1 {c} = {rate} so'm\n"
            return text
        else:
            text = "🌐 **Boshqa Valyutalar:**\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            for i in r[5:25]:
                text += f"🔹 1 {i['Ccy']} = {i['Rate']} so'm\n"
            return text
    except: return "⚠️ Kurslarni yuklashda xatolik."

# --- ASOSIY MENYU (MAXFIYLIK TA'MINLANGAN) ---
def main_menu(uid):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    # Obunachilar uchun ochiq tugmalar
    markup.add("📊 Asosiy Kurslar", "🌐 Boshqa Kurslar")
    markup.add("🏦 Banklar Kursi", "💰 Eng yaxshi kurs")
    markup.add("📍 Yaqin banklar", "✍️ Adminga murojaat")
    
    # Faqat Admin uchun tugmalar
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
    bot.send_message(m.chat.id, "🤖 Salom! Men aqlli moliyaviy kotibman.", reply_markup=main_menu(m.chat.id))

# --- ADMINGA MUROJAAT (OBUNACHILAR UCHUN) ---
@bot.message_handler(func=lambda m: m.text == "✍️ Adminga murojaat")
def contact_admin(m):
    msg = bot.send_message(m.chat.id, "📝 Admin uchun xabaringizni yozing:")
    bot.register_next_step_handler(msg, forward_to_admin)

def forward_to_admin(m):
    bot.send_message(ADMIN_ID, f"📩 **YANGI MUROJAAT:**\n\n👤 Kimdan: {m.from_user.first_name}\n🆔 ID: `{m.chat.id}`\n💬 Xabar: {m.text}", parse_mode="Markdown")
    bot.send_message(m.chat.id, "✅ Rahmat! Xabaringiz adminga yetkazildi.", reply_markup=main_menu(m.chat.id))

# --- ADMIN: STATISTIKA (FAQAT SIZ UCHUN) ---
@bot.message_handler(func=lambda m: m.text == "📈 Statistika" and m.chat.id == ADMIN_ID)
def admin_stats(m):
    db = load_db()
    bot.send_message(ADMIN_ID, f"📊 **BOT STATISTIKASI:**\n👤 Obunachilar: {len(db['users'])}\n👥 Guruhlar: {len(db['groups'])}")

# --- KOTIB: KUNLIK MOLIYAVIY HISOBOT ---
@bot.message_handler(func=lambda m: m.text == "📑 Kunlik Kotib Hisoboti" and m.chat.id == ADMIN_ID)
def secretary_report(m):
    db = load_db()
    reward = db["config"]["reward"]
    report = "📝 **KOTIB HISOBOTI**\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    total = 0
    for uid, data in db["users"].items():
        if data.get("ref_count", 0) > 0:
            summa = data['ref_count'] * reward
            total += summa
            report += f"• `{uid}`: {data['ref_count']} kishi ({summa:,} so'm)\n"
    report += f"\n💰 **Jami to'lov:** {total:,} so'm"
    bot.send_message(ADMIN_ID, report, parse_mode="Markdown")

# --- REKLAMA VA AVTO-OCHIRISH ---
@bot.message_handler(func=lambda m: m.text == "📢 Reklama Joylash" and m.chat.id == ADMIN_ID)
def ad_start(m):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("1 Kun", callback_data="d_1"), types.InlineKeyboardButton("1 Hafta", callback_data="d_7"),
           types.InlineKeyboardButton("1 Oy", callback_data="d_30"), types.InlineKeyboardButton("Kvartal", callback_data="d_90"),
           types.InlineKeyboardButton("1 Yil", callback_data="d_365"))
    bot.send_message(ADMIN_ID, "Reklama muddatini tanlang:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith('d_'))
def ad_save_step(c):
    days = int(c.data.split('_')[1])
    msg = bot.send_message(ADMIN_ID, f"📝 {days} kunlik reklama xabarini yuboring:")
    bot.register_next_step_handler(msg, ad_final_save, days)

def ad_final_save(m, days):
    db = load_db()
    expire_dt = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M")
    db["ads"].append({"msg_id": m.message_id, "expire": expire_dt})
    save_db(db)
    bot.send_message(ADMIN_ID, f"✅ Reklama saqlandi! {expire_dt} da avto-o'chadi.")

def auto_broadcast():
    db = load_db()
    now = datetime.now()
    active_ads = []
    for ad in db["ads"]:
        if datetime.strptime(ad['expire'], "%Y-%m-%d %H:%M") > now:
            active_ads.append(ad)
            for target in list(db["users"].keys()) + list(db["groups"].keys()):
                try: bot.copy_message(target, ADMIN_ID, ad['msg_id'])
                except: pass
    db["ads"] = active_ads
    save_db(db)

# --- BANK VA KURS FUNKSIYALARI ---
@bot.message_handler(func=lambda m: m.text == "📊 Asosiy Kurslar")
def sh_main(m): bot.send_message(m.chat.id, get_cbu_rates("main"), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "💰 Eng yaxshi kurs")
def sh_best(m):
    bot.send_message(m.chat.id, "🕵️ **AI Maslahati:** Bugun USD sotib olish uchun **Anorbank** eng yaxshisi.", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📍 Yaqin banklar")
def geo_req(m):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(types.KeyboardButton("📍 Joylashuvni yuborish", request_location=True))
    bot.send_message(m.chat.id, "Yaqin banklarni topish uchun joylashuvni yuboring:", reply_markup=kb)

@bot.message_handler(content_types=['location'])
def geo_map(m):
    url = f"https://www.google.com/maps/search/bank/@{m.location.latitude},{m.location.longitude},15z"
    bot.send_message(m.chat.id, f"📍 [Xaritani ochish]({url})", parse_mode="Markdown")

# --- SERVER ---
@app.route('/')
def home(): return "AI Secretary is Active"

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    for hour in [9, 15, 21]:
        scheduler.add_job(auto_broadcast, 'cron', hour=hour, minute=0)
    scheduler.start()
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()
    bot.infinity_polling()
