import telebot
import requests
import os
from flask import Flask
import threading

# 1. BOT SOZLAMALARI
TOKEN = "8606825506:AAEzwJZcDmAVad6QQbhLY8RU7bnLzqdf8-g"
ADMIN_ID = 505222809  # Sizning ID raqamingiz
bot = telebot.TeleBot(TOKEN)

# Foydalanuvchilarni saqlash uchun oddiy ro'yxat (bazaga o'rinbosar)
users = set()

# 2. RENDER UCHUN VEB-SERVER
app = Flask(__name__)
@app.route('/')
def home(): return "Bot ishlayapti!"

# 3. VALYUTA KURSLARINI OLISH
def get_rates():
    try:
        url = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/"
        response = requests.get(url, timeout=10)
        return response.json()
    except: return None

# 4. ADMIN TUGMALARI
def admin_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📊 Statistika", "📢 Reklama yuborish")
    markup.add("💰 Valyuta kurslari")
    return markup

# 5. START BUYRUG'I
@bot.message_handler(commands=['start'])
def start(message):
    users.add(message.chat.id)
    if message.chat.id == ADMIN_ID:
        bot.send_message(message.chat.id, "👋 Salom, Admin! Panelga xush kelibsiz.", reply_markup=admin_keyboard())
    else:
        bot.send_message(message.chat.id, "👋 Salom! Valyuta kurslarini ko'rish uchun istalgan xabarni yuboring.")

# 6. ADMIN FUNKSIYALARI VA KURSLAR
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # Statistika
    if message.chat.id == ADMIN_ID and message.text == "📊 Statistika":
        bot.reply_to(message, f"👥 Bot a'zolari soni: {len(users)} ta")
    
    # Reklama yuborish (Tayyorgarlik)
    elif message.chat.id == ADMIN_ID and message.text == "📢 Reklama yuborish":
        msg = bot.reply_to(message, "Yubormoqchi bo'lgan xabaringizni yozing (matn, rasm yoki video):")
        bot.register_next_step_handler(msg, send_reklama)

    # Kurslarni ko'rish
    else:
        rates = get_rates()
        if not rates:
            bot.reply_to(message, "⚠️ Xatolik yuz berdi.")
            return
        
        text = "💰 **MB Kurslari:**\n\n"
        for r in rates:
            if r['Ccy'] in ['USD', 'EUR', 'RUB', 'KZT']:
                text += f"1 {r['Ccy']} = **{r['Rate']}** so'm\n"
        bot.reply_to(message, text, parse_mode="Markdown")

# 7. REKLAMA TARQATISH FUNKSIYASI
def send_reklama(message):
    count = 0
    for user in users:
        try:
            bot.copy_message(user, message.chat.id, message.message_id)
            count += 1
        except: pass
    bot.send_message(ADMIN_ID, f"✅ Reklama {count} ta foydalanuvchiga yuborildi!", reply_markup=admin_keyboard())

# 8. ISHGA TUSHIRISH
if __name__ == "__main__":
    threading.Thread(target=lambda: bot.infinity_polling()).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
