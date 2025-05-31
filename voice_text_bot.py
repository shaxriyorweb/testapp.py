import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from gtts import gTTS
import speech_recognition as sr
from pydub import AudioSegment
from PIL import Image
import pytesseract
from moviepy.editor import VideoFileClip

# ➕ Windows foydalanuvchilari uchun quyidagini oching:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

BOT_TOKEN = "7899690264:AAH14dhEGOlvRoc4CageMH6WYROMEE5NmkY"

user_languages = {}  # user_id: lang

LANG_OPTIONS = {
    "🇺🇿 Uzbek": "uz",
    "🇬🇧 English": "en",
    "🇷🇺 Russian": "ru",
    "🇹🇷 Turkish": "tr"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = ReplyKeyboardMarkup(
        [["🇺🇿 Uzbek", "🇬🇧 English"], ["🇷🇺 Russian", "🇹🇷 Turkish"]],
        resize_keyboard=True
    )
    await update.message.reply_text(
        "Tilni tanlang / Choose your language / Выберите язык / Dil seçin:",
        reply_markup=keyboard
    )

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_choice = update.message.text
    user_id = update.effective_user.id
    if lang_choice in LANG_OPTIONS:
        user_languages[user_id] = LANG_OPTIONS[lang_choice]
        await update.message.reply_text("✅ Til tanlandi! Endi matn, ovoz, rasm yoki video yuboring.")
    else:
        await update.message.reply_text("❌ Noto‘g‘ri tanlov.")

# 🔹 Matn → Ovoz
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = user_languages.get(user_id, "uz")
    text = update.message.text
    tts = gTTS(text, lang=lang)
    tts.save("tts.mp3")
    await update.message.reply_voice(voice=open("tts.mp3", "rb"))
    os.remove("tts.mp3")

# 🔹 Ovoz → Matn
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = user_languages.get(user_id, "uz")
    file = await update.message.voice.get_file()
    await file.download_to_drive("voice.ogg")

    audio = AudioSegment.from_file("voice.ogg")
    audio.export("voice.wav", format="wav")

    r = sr.Recognizer()
    with sr.AudioFile("voice.wav") as source:
        audio_data = r.record(source)
        try:
            text = r.recognize_google(audio_data, language=f"{lang}-{lang.upper()}")
            await update.message.reply_text(f"🗣 Ovozdan matn: {text}")
        except:
            await update.message.reply_text("❌ Ovoz matn sifatida tanilmadi.")
    
    os.remove("voice.ogg")
    os.remove("voice.wav")

# 🔹 Rasm → Matn
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.photo[-1].get_file()
    await file.download_to_drive("photo.jpg")
    try:
        img = Image.open("photo.jpg")
        text = pytesseract.image_to_string(img, lang="uzb+eng+rus+tur")
        await update.message.reply_text(f"🖼 Rasm matni:\n{text.strip() or 'Matn topilmadi.'}")
    except Exception as e:
        await update.message.reply_text("❌ OCRda xatolik.")
        print("OCR error:", e)
    finally:
        os.remove("photo.jpg")

# 🔹 Video → Matn
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = user_languages.get(user_id, "uz")
    file = await update.message.video.get_file()
    await file.download_to_drive("video.mp4")
    try:
        video = VideoFileClip("video.mp4")
        video.audio.write_audiofile("video_audio.wav")

        r = sr.Recognizer()
        with sr.AudioFile("video_audio.wav") as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data, language=f"{lang}-{lang.upper()}")
            await update.message.reply_text(f"🎬 Videodagi nutq: {text}")
    except Exception as e:
        await update.message.reply_text("❌ Video ovozini o‘qishda xatolik.")
        print("Video audio error:", e)
    finally:
        os.remove("video.mp4")
        if os.path.exists("video_audio.wav"):
            os.remove("video_audio.wav")

# 🔸 Run
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^(🇺🇿 Uzbek|🇬🇧 English|🇷🇺 Russian|🇹🇷 Turkish)$"), set_language))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))

    print("🚀 Bot ishga tushdi!")
    app.run_polling()

if __name__ == "__main__":
    main()
