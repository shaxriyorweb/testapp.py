import os
import sqlite3
from telegram import (
    Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler
)
from gtts import gTTS
from pydub import AudioSegment
import speech_recognition as sr

TOKEN = "7899690264:AAH14dhEGOlvRoc4CageMH6WYROMEE5NmkY"
ADMIN_IDS = [7750409176]

CHANNEL_USERNAME ="https://t.me/kichkinashahzodadew"  # <-- Kanal username sini shu yerga yozing (misol: @my_channel2qtf)

conn = sqlite3.connect("user_history.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
    user_id INTEGER,
    username TEXT,
    type TEXT,
    content TEXT,
    lang TEXT
)
""")
conn.commit()

user_lang = {}

TEXTS = {
    "uz": {
        "start": "Assalomu alaykum! Men ovozni matnga va matnni ovozga aylantiruvchi botman.",
        "help": "🎤 Ovoz yuboring – matnga aylantiraman\n📝 Matn yuboring – ovozga aylantiraman\n🌐 Tilni almashtirish uchun: /language",
        "language": "Tilni tanlang:",
        "converted_text": "📝 Matnga aylantirildi:",
        "converted_voice": "🎧 Ovozga aylantirildi.",
        "error": "😔 Ovoz tanib bo‘lmadi. Qaytadan urinib ko‘ring.",
        "subscribe": f"Iltimos, botdan foydalanish uchun kanalimizga obuna bo'ling: {CHANNEL_USERNAME}",
        "subscribe_button": "Kanalga obuna bo‘ling"
    },
    "ru": {
        "start": "Привет! Я бот, который преобразует голос в текст и наоборот.",
        "help": "🎤 Отправьте голос – я превращу в текст\n📝 Отправьте текст – я превращу в голос\n🌐 Сменить язык: /language",
        "language": "Выберите язык:",
        "converted_text": "📝 Преобразованный текст:",
        "converted_voice": "🎧 Преобразовано в голос.",
        "error": "😔 Не удалось распознать речь. Попробуйте ещё раз.",
        "subscribe": f"Пожалуйста, подпишитесь на наш канал, чтобы использовать бота: {CHANNEL_USERNAME}",
        "subscribe_button": "Подписаться на канал"
    },
    "en": {
        "start": "Hello! I'm a bot that converts voice to text and text to voice.",
        "help": "🎤 Send voice – I’ll convert to text\n📝 Send text – I’ll convert to voice\n🌐 Change language: /language",
        "language": "Choose a language:",
        "converted_text": "📝 Converted text:",
        "converted_voice": "🎧 Converted to voice.",
        "error": "😔 Could not recognize the voice. Please try again.",
        "subscribe": f"Please subscribe to our channel to use the bot: {CHANNEL_USERNAME}",
        "subscribe_button": "Subscribe to channel"
    },
    "tr": {
        "start": "Merhaba! Ben sesi metne ve metni sese dönüştüren bir botum.",
        "help": "🎤 Ses gönder – metne dönüştüreyim\n📝 Metin gönder – sese dönüştüreyim\n🌐 Dili değiştirmek için: /language",
        "language": "Dil seçiniz:",
        "converted_text": "📝 Metne dönüştürüldü:",
        "converted_voice": "🎧 Sese dönüştürüldü.",
        "error": "😔 Ses tanınamadı. Lütfen tekrar deneyin.",
        "subscribe": f"Lütfen botu kullanmak için kanalımıza abone olun: {CHANNEL_USERNAME}",
        "subscribe_button": "Kanala abone ol"
    }
}

LANG_KEYBOARD = [["UZ 🇺🇿", "RU 🇷🇺", "EN 🇬🇧", "TR 🇹🇷"]]

def get_lang(user_id):
    return user_lang.get(user_id, "uz")

def save_history(user_id, username, type_, content, lang):
    cursor.execute("INSERT INTO history VALUES (?, ?, ?, ?, ?)",
                   (user_id, username, type_, content, lang))
    conn.commit()

# Check if user is member of the channel
async def is_user_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status != "left"
    except Exception as e:
        print(f"Subscription check error: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_lang(user_id)

    subscribed = await is_user_subscribed(context.bot, user_id)
    if not subscribed:
        # Inline button for channel link
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(text=TEXTS[lang]["subscribe_button"], url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}")
        ]])
        await update.message.reply_text(TEXTS[lang]["subscribe"], reply_markup=keyboard)
        return
    
    await update.message.reply_text(TEXTS[lang]["start"])
    await help_command(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    await update.message.reply_text(TEXTS[lang]["help"])

async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    await update.message.reply_text(
        TEXTS[lang]["language"],
        reply_markup=ReplyKeyboardMarkup(LANG_KEYBOARD, one_time_keyboard=True, resize_keyboard=True)
    )

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_input = update.message.text
    user_id = update.effective_user.id
    if "UZ" in lang_input:
        user_lang[user_id] = "uz"
    elif "RU" in lang_input:
        user_lang[user_id] = "ru"
    elif "EN" in lang_input:
        user_lang[user_id] = "en"
    elif "TR" in lang_input:
        user_lang[user_id] = "tr"
    lang = get_lang(user_id)
    await update.message.reply_text(f"✅ {lang_input} tanlandi.")
    await help_command(update, context)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_lang(user.id)
    
    # Check subscription
    subscribed = await is_user_subscribed(context.bot, user.id)
    if not subscribed:
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(text=TEXTS[lang]["subscribe_button"], url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}")
        ]])
        await update.message.reply_text(TEXTS[lang]["subscribe"], reply_markup=keyboard)
        return

    file = await update.message.voice.get_file()
    file_path = "voice.ogg"
    await file.download_to_drive(file_path)

    audio = AudioSegment.from_ogg(file_path)
    wav_path = "voice.wav"
    audio.export(wav_path, format="wav")

    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_path) as source:
        recognizer.adjust_for_ambient_noise(source)
        audio_data = recognizer.record(source)
        try:
            recog_lang = {
                "uz": "uz-UZ",
                "ru": "ru-RU",
                "en": "en-US",
                "tr": "tr-TR"
            }[lang]
            text = recognizer.recognize_google(audio_data, language=recog_lang)
            await update.message.reply_text(f"{TEXTS[lang]['converted_text']} {text}")
            save_history(user.id, user.username, "voice_to_text", text, lang)
        except Exception as e:
            await update.message.reply_text(TEXTS[lang]["error"])
            print("Speech recognition error:", e)

    os.remove(file_path)
    os.remove(wav_path)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_lang(user.id)
    text = update.message.text

    # Check subscription
    subscribed = await is_user_subscribed(context.bot, user.id)
    if not subscribed:
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(text=TEXTS[lang]["subscribe_button"], url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}")
        ]])
        await update.message.reply_text(TEXTS[lang]["subscribe"], reply_markup=keyboard)
        return

    if text in ["UZ 🇺🇿", "RU 🇷🇺", "EN 🇬🇧", "TR 🇹🇷"]:
        await set_language(update, context)
        return

    try:
        tts = gTTS(text=text, lang=lang)
        tts.save("speech.mp3")
        await update.message.reply_voice(voice=open("speech.mp3", "rb"))
        await update.message.reply_text(TEXTS[lang]["converted_voice"])
        save_history(user.id, user.username, "text_to_voice", text, lang)
        os.remove("speech.mp3")
    except Exception as e:
        await update.message.reply_text("😔 Matndan ovozga aylantirishda xatolik yuz berdi.")
        print("TTS Error:", e)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Sizda bu buyruqdan foydalanish uchun ruxsat yo‘q.")
        return
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM history")
    user_count = cursor.fetchone()[0]
    await update.message.reply_text(f"📊 Botdan foydalangan foydalanuvchilar soni: {user_count}")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("language", language))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(MessageHandler(filters.VOICE, handle_voice))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))

print("Bot ishlashga tayyor!")
app.run_polling()
