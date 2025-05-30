import os
import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)
from gtts import gTTS
from pydub import AudioSegment
import speech_recognition as sr

# 🔐 BOT TOKEN
TOKEN = "7899690264:AAH14dhEGOlvRoc4CageMH6WYROMEE5NmkY"

# 📦 SQLite baza
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

# 🌍 Foydalanuvchi tili sozlamasi
user_lang = {}

# 📌 Har bir til uchun matnlar
TEXTS = {
    "uz": {
        "start": "Assalomu alaykum! Men ovozni matnga va matnni ovozga aylantiruvchi botman.",
        "help": "🎤 Ovoz yuboring – matnga aylantiraman\n📝 Matn yuboring – ovozga aylantiraman\n🌐 Tilni almashtirish uchun: /language",
        "language": "Tilni tanlang:",
        "converted_text": "📝 Matnga aylantirildi:",
        "converted_voice": "🎧 Ovozga aylantirildi.",
        "error": "😔 Ovoz tanib bo‘lmadi. Qaytadan urinib ko‘ring.",
        "tts_error": "😔 Matndan ovozga aylantirishda xatolik yuz berdi."
    },
    "ru": {
        "start": "Привет! Я бот, который преобразует голос в текст и наоборот.",
        "help": "🎤 Отправьте голос – я превращу в текст\n📝 Отправьте текст – я превращу в голос\n🌐 Сменить язык: /language",
        "language": "Выберите язык:",
        "converted_text": "📝 Преобразованный текст:",
        "converted_voice": "🎧 Преобразовано в голос.",
        "error": "😔 Не удалось распознать речь. Попробуйте ещё раз.",
        "tts_error": "😔 Ошибка при преобразовании текста в речь."
    },
    "en": {
        "start": "Hello! I'm a bot that converts voice to text and text to voice.",
        "help": "🎤 Send voice – I’ll convert to text\n📝 Send text – I’ll convert to voice\n🌐 Change language: /language",
        "language": "Choose a language:",
        "converted_text": "📝 Converted text:",
        "converted_voice": "🎧 Converted to voice.",
        "error": "😔 Could not recognize the voice. Please try again.",
        "tts_error": "😔 Error converting text to speech."
    },
    "tr": {
        "start": "Merhaba! Ben sesi metne ve metni sese dönüştüren bir botum.",
        "help": "🎤 Ses gönder – metne dönüştüreyim\n📝 Metin gönder – sese dönüştüreyim\n🌐 Dili değiştirmek için: /language",
        "language": "Dil seçiniz:",
        "converted_text": "📝 Metne dönüştürüldü:",
        "converted_voice": "🎧 Sese dönüştürüldü.",
        "error": "😔 Ses tanınamadı. Lütfen tekrar deneyin.",
        "tts_error": "😔 Metni sese dönüştürürken hata oluştu."
    }
}

# 🌐 Til tanlash klaviaturasi
LANG_KEYBOARD = [["UZ 🇺🇿", "RU 🇷🇺", "EN 🇬🇧", "TR 🇹🇷"]]

def get_lang(user_id):
    return user_lang.get(user_id, "uz")

def save_history(user_id, username, type_, content, lang):
    cursor.execute("INSERT INTO history VALUES (?, ?, ?, ?, ?)",
                   (user_id, username, type_, content, lang))
    conn.commit()

# 🔹 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # Default tilni o‘rnatish agar yo‘q bo‘lsa
    if user_id not in user_lang:
        user_lang[user_id] = "uz"
    lang = get_lang(user_id)
    await update.message.reply_text(TEXTS[lang]["start"])
    await help_command(update, context)

# 🔹 /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    await update.message.reply_text(TEXTS[lang]["help"])

# 🔹 /language
async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    await update.message.reply_text(
        TEXTS[lang]["language"],
        reply_markup=ReplyKeyboardMarkup(LANG_KEYBOARD, one_time_keyboard=True, resize_keyboard=True)
    )

# 🔹 Til tanlash
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

# 🔹 VOICE → TEXT
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_lang(user.id)

    file = await update.message.voice.get_file()
    file_path = f"voice_{user.id}.ogg"
    await file.download_to_drive(file_path)

    audio = AudioSegment.from_ogg(file_path)
    wav_path = f"voice_{user.id}.wav"
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

    # Fayllarni o'chirish
    if os.path.exists(file_path):
        os.remove(file_path)
    if os.path.exists(wav_path):
        os.remove(wav_path)

# 🔹 TEXT → VOICE
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_lang(user.id)
    text = update.message.text

    # Til tanlash tugmalari
    if text in ["UZ 🇺🇿", "RU 🇷🇺", "EN 🇬🇧", "TR 🇹🇷"]:
        await set_language(update, context)
        return

    try:
        # gTTS uchun til kodi boshqacha (uzbek uchun 'uz' emas, 'uz' ni google gTTS to‘liq qo‘llamaydi,
        # shuning uchun 'uz' o‘rniga 'en' ishlatamiz yoki turkcha 'tr' agar kerak bo‘lsa)
        tts_lang_map = {
            "uz": "en",  # gTTS uzbek tilini to‘liq qo‘llamaydi, shuning uchun ingliz tilida ovoz chiqadi
            "ru": "ru",
            "en": "en",
            "tr": "tr"
        }
        tts_lang = tts_lang_map.get(lang, "en")

        tts = gTTS(text=text, lang=tts_lang)
        audio_path = f"speech_{user.id}.mp3"
        tts.save(audio_path)
        await update.message.reply_voice(voice=open(audio_path, "rb"))
        await update.message.reply_text(TEXTS[lang]["converted_voice"])
        save_history(user.id, user.username, "text_to_voice", text, lang)
        if os.path.exists(audio_path):
            os.remove(audio_path)
    except Exception as e:
        await update.message.reply_text(TEXTS[lang]["tts_error"])
        print("TTS Error:", e)

# 🧠 BOT START
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("language", language))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))

print("🤖 Bot ishga tushdi...")
app.run_polling()
