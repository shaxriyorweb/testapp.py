import json
import os
from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)
from telegram.error import BadRequest

# 🔧 Fayl nomi
USER_DATA_FILE = "user_data.json"
CHANNEL_USERNAME = "2632823715"

# 🌐 Matnlar
TEXTS = {
    "start": {
        "uz": "👋 Assalomu alaykum! Botdan foydalanish uchun quyidagi tugmalarni tanlang.",
        "ru": "👋 Здравствуйте! Используйте кнопки ниже для навигации.",
        "en": "👋 Hello! Use the buttons below to navigate.",
        "tr": "👋 Merhaba! Aşağıdaki düğmeleri kullanın."
    },
    "not_subscribed": {
        "uz": f"❗ Botdan foydalanish uchun avval kanalga obuna bo‘ling:\n{CHANNEL_USERNAME}",
        "ru": f"❗ Пожалуйста, сначала подпишитесь на канал:\n{CHANNEL_USERNAME}",
        "en": f"❗ Please subscribe to the channel first:\n{CHANNEL_USERNAME}",
        "tr": f"❗ Lütfen önce kanala abone olun:\n{CHANNEL_USERNAME}"
    },
    "help": {
        "uz": "🆘 Yordam: Savollar bo‘lsa shu yerga yozing.",
        "ru": "🆘 Помощь: Напишите сюда, если есть вопросы.",
        "en": "🆘 Help: Write here if you have any questions.",
        "tr": "🆘 Yardım: Sorularınız varsa buraya yazın."
    },
    "stats": {
        "uz": "📊 Foydalanuvchilar soni:",
        "ru": "📊 Количество пользователей:",
        "en": "📊 Number of users:",
        "tr": "📊 Kullanıcı sayısı:"
    },
    "language_changed": {
        "uz": "✅ Til o‘zgaritildi: O‘zbekcha",
        "ru": "✅ Язык изменён: Русский",
        "en": "✅ Language changed: English",
        "tr": "✅ Dil değiştirildi: Türkçe"
    }
}

# 📁 Foydalanuvchilarni JSON faylda saqlash
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_user_data(data):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(data, f)

# 🌐 Foydalanuvchi tilini aniqlash
def get_lang(update: Update):
    code = update.effective_user.language_code or "uz"
    if code.startswith("ru"):
        return "ru"
    elif code.startswith("en"):
        return "en"
    elif code.startswith("tr"):
        return "tr"
    else:
        return "uz"

# ✅ Obuna tekshirish
async def is_subscribed(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'creator', 'administrator']
    except BadRequest:
        return False

# 🧭 Inline tugmalar
def get_keyboard(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Statistika", callback_data="stats")],
        [InlineKeyboardButton("🆘 Yordam", callback_data="help")],
        [InlineKeyboardButton("🔁 Tilni o‘zgartirish", callback_data="change_lang")]
    ])

# 🚀 /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_lang(update)

    if not await is_subscribed(user_id, context):
        await update.message.reply_text(TEXTS["not_subscribed"][lang])
        return

    # 👤 Foydalanuvchini saqlash
    user_data = load_user_data()
    user_data[str(user_id)] = lang
    save_user_data(user_data)

    await update.message.reply_text(
        TEXTS["start"][lang],
        reply_markup=get_keyboard(lang)
    )

# 🎛 Tugmalar ustida ishlov
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_data = load_user_data()
    lang = user_data.get(str(user_id), "uz")

    if query.data == "stats":
        total_users = len(user_data)
        await query.edit_message_text(f"{TEXTS['stats'][lang]} {total_users}")
    elif query.data == "help":
        await query.edit_message_text(TEXTS["help"][lang])
    elif query.data == "change_lang":
        # 🔄 Tilni aylantirish
        langs = ["uz", "ru", "en", "tr"]
        current_index = langs.index(lang)
        new_lang = langs[(current_index + 1) % len(langs)]
        user_data[str(user_id)] = new_lang
        save_user_data(user_data)
        await query.edit_message_text(TEXTS["language_changed"][new_lang])

# ✉️ Matnli xabarlar (ixtiyoriy)
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass  # Istasangiz bu yerga xabar qabul qilishni yozish mumkin

# 🧠 Asosiy funksiya
async def main():
    app = ApplicationBuilder().token("7899690264:AAH14dhEGOlvRoc4CageMH6WYROMEE5NmkY").build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("🤖 Bot ishga tushdi...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
