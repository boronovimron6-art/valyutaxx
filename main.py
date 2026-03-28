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
                    db["config"] = {"reward": 500, "prices": {"kun": "50k", "hafta": "300k"}}
                return db
            except: return {"users": {}, "groups": {}, "ads": [], "config": {"reward": 500}}
    return {"users": {}, "groups": {}, "ads": [], "config": {"reward": 500}}

def save_db(data):
    with open("ai_master_db.json", "w") as f:
        json.dump(data, f, indent=4)

# --- VALYUTA FUNKSIYALARI (CBU MANBASI) ---
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
            text = "🌐 **Boshqa Valyutalar:**\n"
            for i in r[5:25]:
                text += f"🔹 1 {i['Ccy']} = {i['Rate']} so'm\n"
            return text
    except: return "⚠️ Ma'lumot olishda xatolik."

# --- ASOSIY MENYU ---
def main_menu(uid):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📊 Asosiy Kurslar", "🌐 Boshqa Kurslar")
    markup.add("🏦 Banklar Kursi", "💰 Eng yaxshi kurs")
    markup.add("📍 Yaqin banklar", "📈 Statistika")
    
    if uid == ADMIN_ID:
        markup.add("📑 Kunlik Kotib Hisoboti", "💡 AI Biznes Maslahati")
        markup.add("📢 Reklama Joylash", "⚙️ Mukofotni Sozlash")
    else:
        markup.add("💬 AI bilan suhbat")
    return markup

# --- START VA REFERAL TIZIMI ---
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
        
    bot.send_message(m.chat.id, "🤖 Salom! Men sizning aqlli kotibingiz va moliyaviy yordamchingizman.", reply_markup=main_menu(m.chat.id))

# --- KOTIB: KUNLIK HISOBOT (FAQAT ADMIN) ---
@bot.message_handler(func=lambda m: m.text == "📑 Kunlik Kotib Hisoboti" and m.chat.id == ADMIN_ID)
def secretary_report(m):
    db = load_db()
    reward = db["config"]["reward"]
    report = f"📝 **KOTIB: BUGUNGI MOLIYAVIY HISOBOT**\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    report += f"👤 Obunachilar: {len(db['users'])}\n👥 Guruhlar: {len(db['groups'])}\n\n"
    report += "💸 **REFERAL TO'LOVLARI:**\n"
    
    total_pay = 0
    for uid, data in db["users"].items():
        if data.get("ref_count", 0) > 0:
            summa = data['ref_count'] * reward
            total_pay += summa
            report += f"• ID: `{uid}` -> {data['ref_count']} ta obunachi qo'shdi ({summa:,} so'm)\n"
    
    report += f"\n💰 **Jami chiqim:** {total_pay:,} so'm"
    bot.send_message(ADMIN_ID, report, parse_mode="Markdown")

# --- MASLAHATCHI: STRATEGIK TAVSIYALAR ---
@bot.message_handler(func=lambda m: m.text == "💡 AI Biznes Maslahati" and m.chat.id == ADMIN_ID)
def ai_consultant(m):
    db = load_db()
    u_count = len(db["users"])
    advice = "💡 **AI MASLAHATCHI TAHLILI**\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    if u_count < 5000:
        advice += f"📈 Hozircha auditoriya {u_count} ta. 5000 ga yetish uchun mukofotni kamaytirmang.\n• Taklif: Kunlik reklama narxini 50,000 so'mda ushlab turing."
    else:
        advice += "🚀 Auditoriya 5000+! Endi reklamalarni qimmatroq (100k+) sotishni va 'Premium' paketlarni taklif qilishni maslahat beraman."
    bot.send_message(ADMIN_ID, advice, parse_mode="Markdown")

# --- MUKOFOTNI SOZLASH (ADMIN) ---
@bot.message_handler(func=lambda m: m.text == "⚙️ Mukofotni Sozlash" and m.chat.id == ADMIN_ID)
def set_reward_call(m):
    msg = bot.send_message(ADMIN_ID, "Yangi mukofot miqdorini yozing (faqat raqam):")
    bot.register_next_step_handler(msg, save_reward_config)

def save_reward_config(m):
    db = load_db()
    try:
        db["config"]["reward"] = int(m.text)
        save_db(db)
        bot.send_message(ADMIN_ID, f"✅ Kotib: Mukofot {m.text} so'mga o'zgartirildi.")
    except: bot.send_message(ADMIN_ID, "❌ Xato! Faqat raqam kiriting.")

# --- LOKATSIYA: YAQIN BANKLAR ---
@bot.message_handler(func=lambda m: m.text == "📍 Yaqin banklar")
def geo_request(m):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(types.KeyboardButton("📍 Joylashuvni yuborish", request_location=True))
    bot.send_message(m.chat.id, "Yaqin atrofdagi banklarni topish uchun joylashuvni yuboring:", reply_markup=kb)

@bot.message_handler(content_types=['location'])
def find_banks(m):
    url = f"https://www.google.com/maps/search/bank/@{m.location.latitude},{m.location.longitude},15z"
    bot.send_message(m.chat.id, f"📍 Atrofingizdagi banklar xaritada:\n[Google Maps-da ko'rish]({url})", parse_mode="Markdown", reply_markup=main_menu(m.chat.id))

# --- REKLAMA BOSHQARUVI ---
@bot.message_handler(func=lambda m: m.text == "📢 Reklama Joylash" and m.chat.id == ADMIN_ID)
def ad_menu(m):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("1 Kun", callback_data="d_1"), types.InlineKeyboardButton("1 Hafta", callback_data="d_7"),
           types.InlineKeyboardButton("1 Oy", callback_data="d_30"), types.InlineKeyboardButton("Kvartal", callback_data="d_90"),
           types.InlineKeyboardButton("1 Yil", callback_data="d_365"))
    bot.send_message(ADMIN_ID, "🕒 Reklama muddatini tanlang:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith('d_'))
def ad_receive_step(c):
    days = int(c.data.split('_')[1])
    msg = bot.send_message(ADMIN_ID, f"📝 {days} kunlik reklama xabarini yuboring (1xbet/Pornografiya taqiqlangan!):")
    bot.register_next_step_handler(msg, ad_save_final, days)

def ad_save_final(m, days):
    db = load_db()
    expire_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M")
    db["ads"].append({"msg_id": m.message_id, "expire": expire_date})
    save_db(db)
    bot.send_message(ADMIN_ID, f"✅ Reklama qabul qilindi! {expire_date} gacha avtomatik tarqatiladi.")

# --- AVTOMATIK REKLAMA TARQATISH (3 MAHAL) ---
def ai_auto_broadcast():
    db = load_db()
    now = datetime.now()
    valid_ads = []
    for ad in db["ads"]:
        if datetime.strptime(ad['expire'], "%Y-%m-%d %H:%M") > now:
            valid_ads.append(ad)
            # Guruhlarga va foydalanuvchilarga tarqatish
            for uid in list(db["users"].keys()) + list(db["groups"].keys()):
                try: bot.copy_message(uid, ADMIN_ID, ad['msg_id'])
                except: pass
    db["ads"] = valid_ads
    save_db(db)

# --- QOLGAN TUGMALAR ---
@bot.message_handler(func=lambda m: m.text == "📊 Asosiy Kurslar")
def sh_rates(m): bot.send_message(m.chat.id, get_cbu_rates("main"), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🌐 Boshqa Kurslar")
def sh_other_rates(m): bot.send_message(m.chat.id, get_cbu_rates("other"), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🏦 Banklar Kursi")
def sh_banks(m):
    text = "🏦 **Banklardagi USD sotish kursi:**\n\n🏢 NBU: 12,965\n🏢 Kapital: 12,980\n🏢 Hamkor: 12,975\n🏢 Ipak Yo'li: 12,970\n\n⚠️ Manba: Banklarning rasmiy sayti."
    bot.send_message(m.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "💰 Eng yaxshi kurs")
def sh_best(m):
    bot.send_message(m.chat.id, "🕵️ **AI Tahlili:**\n\nBugun dollar sotib olish uchun **Anorbank** eng ma'qul (12,985). Sotish uchun esa **NBU** (12,960).\n\n💡 *Kotib maslahati: Doim xaritadan yaqinroq bankni ham tekshiring.*", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📈 Statistika")
def sh_stats(m):
    db = load_db()
    bot.send_message(m.chat.id, f"📊 **Statistika:**\n👤 Shaxsiy obunachilar: {len(db['users'])}\n👥 Faol guruhlar: {len(db['groups'])}\n📡 Tizim: 24/7 AI Online")

@bot.message_handler(func=lambda m: m.chat.type == 'private')
def ai_chat(m):
    bot.reply_to(m, "🤖 Salom! Men sizning moliyaviy kotibingizman. Kurslar yoki banklar haqida savolingiz bo'lsa, menyudan foydalaning.")

# --- SERVER ---
@app.route('/')
def home(): return "AI Secretary & Finance System is Online"

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    # Kuniga 3 marta reklama (09:00, 15:00, 21:00)
    for h in [9, 15, 21]:
        scheduler.add_job(ai_auto_broadcast, 'cron', hour=h, minute=0)
    scheduler.start()
    
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()
    bot.infinity_polling()
