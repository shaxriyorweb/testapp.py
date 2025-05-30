import os
import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)
from gtts import gTTS
from pydub import AudioSegment
import speech_recognition as sr

TOKEN = "7899690264:AAH14dhEGOlvRoc4CageMH6WYROMEE5NmkY"

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
        "help": "🎤 Ovoz yuboring – matnga aylantiraman\n📝 Matn yuboring – ovozga aylantiraman\n🎵 Musiqa nomini yuboring – musiqa olasiz\n🌐 Tilni almashtirish uchun: /language",
        "language": "Tilni tanlang:",
        "converted_text": "📝 Matnga aylantirildi:",
        "converted_voice": "🎧 Ovozga aylantirildi.",
        "error": "😔 Ovoz tanib bo‘lmadi yoki noto‘g‘ri til.",
        "wrong_lang": "❌ Iltimos, faqat tanlangan tilda xabar yuboring.",
        "music_not_found": "❌ Bu nomdagi musiqa topilmadi.",
        "language_set": "✅ {} tili tanlandi."
    },
    "ru": {
        "start": "Привет! Я бот, который преобразует голос в текст и текст в голос.",
        "help": "🎤 Отправьте голос – я превращу в текст\n📝 Отправьте текст – я превращу в голос\n🎵 Отправьте название песни – получите музыку\n🌐 Сменить язык: /language",
        "language": "Выберите язык:",
        "converted_text": "📝 Преобразованный текст:",
        "converted_voice": "🎧 Преобразовано в голос.",
        "error": "😔 Не удалось распознать речь или неверный язык.",
        "wrong_lang": "❌ Пожалуйста, отправляйте сообщения только на выбранном языке.",
        "music_not_found": "❌ Музыка с таким названием не найдена.",
        "language_set": "✅ Выбран язык {}."
    },
    "en": {
        "start": "Hello! I'm a bot that converts voice to text and text to voice.",
        "help": "🎤 Send voice – I’ll convert to text\n📝 Send text – I’ll convert to voice\n🎵 Send a song name – get music\n🌐 Change language: /language",
        "language": "Choose a language:",
        "converted_text": "📝 Converted text:",
        "converted_voice": "🎧 Converted to voice.",
        "error": "😔 Could not recognize voice or wrong language.",
        "wrong_lang": "❌ Please send messages only in the selected language.",
        "music_not_found": "❌ Music with this name not found.",
        "language_set": "✅ {} language selected."
    },
    "tr": {
        "start": "Merhaba! Ben sesi metne ve metni sese dönüştüren bir botum.",
        "help": "🎤 Ses gönder – metne dönüştüreyim\n📝 Metin gönder – sese dönüştüreyim\n🎵 Şarkı adı gönder – müzik al\n🌐 Dili değiştirmek için: /language",
        "language": "Dil seçiniz:",
        "converted_text": "📝 Metne dönüştürüldü:",
        "converted_voice": "🎧 Sese dönüştürüldü.",
        "error": "😔 Ses tanınamadı veya yanlış dil.",
        "wrong_lang": "❌ Lütfen sadece seçilen dilde mesaj gönderin.",
        "music_not_found": "❌ Bu isimde müzik bulunamadı.",
        "language_set": "✅ {} dili seçildi."
    }
}

LANG_KEYBOARD = [["UZ 🇺🇿", "RU 🇷🇺", "EN 🇬🇧", "TR 🇹🇷"]]

# Musiqa fayllari (misol uchun nom va fayl nomi)
MUSIC_FILES = {
    "uz": {
        "musiqa1": "music/uz/musiqa1.mp3",
        "musiqa2": "music/uz/musiqa2.mp3",
    },
    "ru": {
        "песня1": "music/ru/pesnya1.mp3",
        "песня2": "music/ru/pesnya2.mp3",
    },
    "en": {
        "song1": "music/en/song1.mp3",
        "song2": "music/en/song2.mp3",
    },
    "tr": {
        "sarki1": "music/tr/sarki1.mp3",
        "sarki2": "music/tr/sarki2.mp3",
    }
}

def get_lang(user_id):
    return user_lang.get(user_id, "uz")

def save_history(user_id, username, type_, content, lang):
    cursor.execute("INSERT INTO history VALUES (?, ?, ?, ?, ?)",
                   (user_id, username, type_, content, lang))
    conn.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
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
    await update.message.reply_text(TEXTS[lang]["language_set"].format(lang_input))
    await help_command(update, context)

# Til kodi SpeechRecognition uchun (STT)
recog_lang = {
    "uz": "en-US",  # O'zbek tilini inglizcha kod bilan ishlatamiz
    "ru": "ru-RU",
    "en": "en-US",
    "tr": "tr-TR"
}

# Til kodi gTTS uchun (TTS)
tts_lang = {
    "uz": "en",
    "ru": "ru",
    "en": "en",
    "tr": "tr"
}

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
            text = recognizer.recognize_google(audio_data, language=recog_lang[lang])
            # Tekshirish: matn faqat tanlangan tilga mos kelishi kerak
            # (Soddaligi uchun, faqat lug'atdagi kalit so'zlarni tekshirish mumkin)
            # Shu yerga o'zingiz tilga mos tekshiruv qo'shishingiz mumkin
            if not is_text_correct_language(text, lang):
                await update.message.reply_text(TEXTS[lang]["wrong_lang"])
            else:
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
    text = update.message.text.strip().lower()

    # Musiqa so'rovi tekshiruvi
    if text in MUSIC_FILES.get(lang, {}):
        music_path = MUSIC_FILES[lang][text]
        if os.path.exists(music_path):
            await update.message.reply_audio(audio=open(music_path, "rb"))
            save_history(user.id, user.username, "music", text, lang)
        else:
            await update.message.reply_text(TEXTS[lang]["music_not_found"])
        return

    # Matn faqat tanlangan tilga mos kelishi kerak (bu yerda oddiy tekshiruv)
    if not is_text_correct_language(text, lang):
        await update.message.reply_text(TEXTS[lang]["wrong_lang"])
        return

    try:
        tts = gTTS(text=text, lang=tts_lang[lang])
        tts.save("tts.mp3")
        await update.message.reply_audio(audio=open("tts.mp3", "rb"))
        save_history(user.id, user.username, "text_to_voice", text, lang)
        os.remove("tts.mp3")
    except Exception as e:
        await update.message.reply_text(TEXTS[lang]["error"])
        print("TTS error:", e)

def is_text_correct_language(text: str, lang: str) -> bool:
    # Bu yerda siz tilga mos kelishini tekshiruvchi sodda funksiya yozing.
    # Misol uchun, harf to'plamiga qarab yoki maxsus kalit so'zlar bo'yicha.
    # Hozircha oddiy tekshiruv: o‘zbek uchun lotin harflari, rus uchun kirill, ingliz uchun lotin, turk uchun lotin.

    if lang == "uz":
        # O‘zbek uchun faqat lotin harflari va bo‘sh joylar
        return all(c.isalpha() or c.isspace() for c in text)
    elif lang == "ru":
        # Rus tilida kirill harflaridan bo‘lishi kerak
        return any('а' <= c <= 'я' or 'А' <= c <= 'Я' for c in text)
    elif lang == "en":
        # Ingliz uchun lotin harflari
        return all(c.isascii() and (c.isalpha() or c.isspace()) for c in text)
    elif lang == "tr":
        # Turkiy til uchun lotin harflari va o'ziga xos harflar: ç, ğ, ı, ö, ş, ü
        allowed = "abcçdefgğhıijklmnoöprsştuüvyz "
        return all(c.lower() in allowed for c in text)
    return False

def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("language", language))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), set_language))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))

    print("Bot ishga tushdi...")
    application.run_polling()

if __name__ == "__main__":
    main()
