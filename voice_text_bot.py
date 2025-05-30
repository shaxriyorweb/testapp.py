import os
import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)
from gtts import gTTS
from pydub import AudioSegment
import speech_recognition as sr
from langdetect import detect, LangDetectException  # <-- til aniqlash uchun

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
        "wrong_lang": "❌ Iltimos, faqat tanlangan tilingizda yozing."
    },
    "ru": {
        "start": "Привет! Я бот, который преобразует голос в текст и наоборот.",
        "help": "🎤 Отправьте голос – я превращу в текст\n📝 Отправьте текст – я превращу в голос\n🌐 Сменить язык: /language",
        "language": "Выберите язык:",
        "converted_text": "📝 Преобразованный текст:",
        "converted_voice": "🎧 Преобразовано в голос.",
        "error": "😔 Не удалось распознать речь. Попробуйте ещё раз.",
        "wrong_lang": "❌ Пожалуйста, пишите только на выбранном языке."
    },
    "en": {
        "start": "Hello! I'm a bot that converts voice to text and text to voice.",
        "help": "🎤 Send voice – I’ll convert to text\n📝 Send text – I’ll convert to voice\n🌐 Change language: /language",
        "language": "Choose a language:",
        "converted_text": "📝 Converted text:",
        "converted_voice": "🎧 Converted to voice.",
        "error": "😔 Could not recognize the voice. Please try again.",
        "wrong_lang": "❌ Please write only in your selected language."
    },
    "tr": {
        "start": "Merhaba! Ben sesi metne ve metni sese dönüştüren bir botum.",
        "help": "🎤 Ses gönder – metne dönüştüreyim\n📝 Metin gönder – sese dönüştüreyim\n🌐 Dili değiştirmek için: /language",
        "language": "Dil seçiniz:",
        "converted_text": "📝 Metne dönüştürüldü:",
        "converted_voice": "🎧 Sese dönüştürüldü.",
        "error": "😔 Ses tanınamadı. Lütfen tekrar deneyin.",
        "wrong_lang": "❌ Lütfen sadece seçilen dilde yazın."
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

# Til kodi uchun langdetect kodi mapping
LANGDETECT_CODES = {
    "uz": "uz",
    "ru": "ru",
    "en": "en",
    "tr": "tr"
}

# 🔹 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
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

# Matn tilini aniqlash va tanlangan til bilan solishtirish
def is_text_in_user_lang(text: str, user_lang_code: str) -> bool:
    try:
        detected_lang = detect(text)
        # Detected lang qisman mos bo'lishi mumkin
        # LangDetect ba'zida "en" emas "en-US" kabi beradi, biz faqat birinchi ikki harfni solishtiramiz
        return detected_lang[:2] == LANGDETECT_CODES[user_lang_code][:2]
    except LangDetectException:
        # Til aniqlanmasa yoki juda qisqa matn bo'lsa
        return False

# 🔹 VOICE → TEXT
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_lang(user.id)

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
            # Ovoz tanilgan matn ham foydalanuvchi tiliga mos bo'lishi kerak
            if not is_text_in_user_lang(text, lang):
                await update.message.reply_text(TEXTS[lang]["wrong_lang"])
            else:
                await update.message.reply_text(f"{TEXTS[lang]['converted_text']} {text}")
                save_history(user.id, user.username, "voice_to_text", text, lang)
        except Exception as e:
            await update.message.reply_text(TEXTS[lang]["error"])
            print("Speech recognition error:", e)

    os.remove(file_path)
    os.remove(wav_path)

# 🔹 TEXT → VOICE
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_lang(user.id)
    text = update.message.text

    if text in ["UZ 🇺🇿", "RU 🇷🇺", "EN 🇬🇧", "TR 🇹🇷"]:
        await set_language(update, context)
        return

    # Matn tilini tekshirish
    if not is_text_in_user_lang(text, lang):
        await update.message.reply_text(TEXTS[lang]["wrong_lang"])
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

# 🧠 BOT START
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("language", language))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))

print("🤖 Bot ishga tushdi...")
app.run_polling()
