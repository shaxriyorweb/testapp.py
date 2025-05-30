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
