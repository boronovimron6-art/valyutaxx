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

# --- FAYLLAR BILAN ISHLASH (USER VA GURUHLAR BAZASI) ---
def get_list(file_name):
    try:
        with open(file_name, "r") as f:
            return f.read().splitlines()
    except:
        return []

def save_id(file_name, target_id):
    ids = get_list(file_name)
    if str(target_id) not in ids:
        with open(file_name, "a") as f:
            f.write(str(target_id) + "\n")

# --- VALYUTA MA'LUMOTLARINI OLISH ---
def get_data():
    try:
        url = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/"
        r = requests.get(url).json()
        usd = next(i['Rate'] for i in r if i['Ccy'] == 'USD')
        eur = next(i['Rate'] for i in r if i['Ccy'] == 'EUR')
        rub = next(i['Rate'] for i in r if i['Ccy'] == 'RUB')
        
        text = f"✨ **BUGUNGI RASMIY KURSLAR** ✨\n"
        text += f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        text += f"🇺🇸 **USD:** {usd} so'm\n"
        text += f"🇪🇺 **EUR:** {eur} so'm\n"
        text += f"🇷🇺 **RUB:** {rub} so'm\n"
        text += f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        text += f"📅 Sana: {r[0]['Date']}\n\n✅ @{bot.get_me().username} orqali olindi"
        return text
    except:
        return "⚠️ Ma'lumot olishda xatolik."

# --- AVTO-REKLAMA FUNKSIYASI ---
def run_group_marketing():
    groups = get_list("groups.txt")
    if not groups: return
    
    ads = [
        "💰 Eng aniq valyuta kurslarini bizning botda kuzating!",
        "📊 Dollarning bugungi narxi qancha? Botga kiring!",
        "🧮 Valyuta hisoblash uchun eng qulay kalkulyator bizda!"
    ]
    ad_text = random.choice(ads)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🚀 Botga kirish", url=f"https://t.me/{bot.get_me().username}"))
    
    for g_id in groups:
        try:
            bot.send_message(g_id, ad_text, reply_markup=markup)
        except: pass

# --- ASOSIY MENYU ---
def main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🔄 Yangilash", "🧮 Kalkulyator")
    markup.add("🏦 Banklar kursi", "🌍 Boshqa valyutalar")
    if str(user_id) == str(ADMIN_ID):
        markup.add("📊 Statistika", "📢 Reklamani Yoqish", "🛑 To'xtatish")
    return markup

# --- START BUYRUG'I ---
@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.type == 'private':
        save_id("users.txt", message.chat.id)
        bot.send_message(message.chat.id, get_data(), parse_mode="Markdown", reply_markup=main_menu(message.chat.id))
    else:
        save_id("groups.txt", message.chat.id)
        bot.send_message(message.chat.id, "Bot guruhda faol! Kurslarni bilish uchun 'dollar' yoki 'kurs' deb yozing.")

# --- GURUHLARDA KALIT SO'ZLARNI TUTISH ---
@bot.message_handler(func=lambda m: m.chat.type != 'private' and any(word in m.text.lower() for word in ['dollar', 'kurs', 'narx', 'valyuta']))
def group_reply(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💰 Shaxsiyda ko'rish", url=f"https://t.me/{bot.get_me().username}?start=info"))
    bot.reply_to(message, "Valyuta kurslarini batafsil ko'rish uchun botga kiring! 👇", reply_markup=markup)

# --- KALKULYATOR ---
@bot.message_handler(func=lambda m: m.text == "🧮 Kalkulyator")
def calc_start(m):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("🇺🇸 USD", callback_data="calc_USD"),
               types.InlineKeyboardButton("🇪🇺 EUR", callback_data="calc_EUR"))
    bot.send_message(m.chat.id, "Qaysi valyutani so'mga aylantiramiz?", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith('calc_'))
def callback_calc(c):
    val = c.data.split('_')[1]
    bot.answer_callback_query(c.id)
    msg = bot.send_message(c.message.chat.id, f"{val} miqdorini kiriting (Masalan: 100):")
    bot.register_next_step_handler(msg, process_calc, val)

def process_calc(m, val):
    try:
        amt = float(m.text)
        r = requests.get("https://cbu.uz/uz/arkhiv-kursov-valyut/json/").json()
        rate = float(next(i['Rate'] for i in r if i['Ccy'] == val))
        bot.send_message(m.chat.id, f"✅ {amt} {val} = **{amt*rate:,.2f} so'm**", parse_mode="Markdown")
    except:
        bot.send_message(m.chat.id, "⚠️ Faqat raqam kiriting!")

# --- ODDIY TUGMALAR ---
@bot.message_handler(func=lambda m: m.text == "🔄 Yangilash")
def refresh(m):
    bot.send_message(m.chat.id, get_data(), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🏦 Banklar kursi")
def banks(m):
    text = "🏦 **Banklarda USD sotuv narxi (Taxminiy):**\n\n🏢 NBU: 12,915\n🏢 Kapitalbank: 12,940\n🏢 Hamkorbank: 12,930"
    bot.send_message(m.chat.id, text, parse_mode="Markdown")

# --- ADMIN PANEL ---
@bot.message_handler(func=lambda m: m.text == "📢 Reklamani Yoqish" and m.chat.id == ADMIN_ID)
def start_ads(m):
    scheduler.add_job(run_group_marketing, 'interval', hours=3, id="marketing_job", replace_existing=True)
    bot.send_message(ADMIN_ID, "✅ Guruhlarda avto-reklama yoqildi (Har 3 soatda).")

@bot.message_handler(func=lambda m: m.text == "🛑 To'xtatish" and m.chat.id == ADMIN_ID)
def stop_ads(m):
    try:
        scheduler.remove_job("marketing_job")
        bot.send_message(ADMIN_ID, "🛑 Reklama to'xtatildi.")
    except:
        bot.send_message(ADMIN_ID, "Faol reklama topilmadi.")

@bot.message_handler(func=lambda m: m.text == "📊 Statistika" and m.chat.id == ADMIN_ID)
def show_stats(m):
    u = len(get_list("users.txt"))
    g = len(get_list("groups.txt"))
    bot.send_message(ADMIN_ID, f"📊 **Statistika:**\n👤 Obunachilar: {u}\n👥 Guruhlar: {g}")

# --- SERVER QISMI (RENDER UCHUN) ---
@app.route('/')
def home(): return "Bot is Active"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.infinity_polling()
