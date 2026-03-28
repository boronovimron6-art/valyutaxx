import telebot
import requests

# Yangi tokenni shu yerga joyladim
TOKEN = "8606825506:AAEzwJZcDmAVad6QQbhLY8RU7bnLzqdf8-g"
bot = telebot.TeleBot(TOKEN)

# Markaziy bankdan valyuta kurslarini olish funksiyasi
def get_rates():
    try:
        url = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")
        return None

# /start buyrug'i uchun handler
@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = (
        f"👋 Salom! @OsonValyutaBot ga xush kelibsiz.\n\n"
        f"🆔 Sizning ID raqamingiz: `{message.chat.id}`\n\n"
        f"📊 Valyuta kurslarini ko'rish uchun istalgan xabarni yuboring yoki menyudan foydalaning."
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

# Barcha matnli xabarlar uchun handler (kurslarni chiqaradi)
@bot.message_handler(func=lambda message: True)
def send_rates(message):
    rates = get_rates()
    if not rates:
        bot.reply_to(message, "⚠️ Ma'lumot olishda xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.")
        return
    
    text = "💰 **O'zbekiston Respublikasi Markaziy Banki kursi bo'yicha:**\n\n"
    
    # Asosiy 4 ta valyutani saralab olamiz
    target_currencies = ['USD', 'EUR', 'RUB', 'KZT']
    
    for r in rates:
        if r['Ccy'] in target_currencies:
            # Bayroqlarni qo'shamiz
            flag = ""
            if r['Ccy'] == 'USD': flag = "🇺🇸"
            elif r['Ccy'] == 'EUR': flag = "🇪🇺"
            elif r['Ccy'] == 'RUB': flag = "🇷🇺"
            elif r['Ccy'] == 'KZT': flag = "🇰🇿"
            
            text += f"{flag} 1 {r['Ccy']} = **{r['Rate']}** so'm\n"
    
    text += f"\n📅 Sana: {rates[0]['Date']}"
    bot.reply_to(message, text, parse_mode="Markdown")

# Botni uzluksiz ishlatish
if __name__ == "__main__":
    print("Bot muvaffaqiyatli ishga tushdi...")
    bot.infinity_polling()
