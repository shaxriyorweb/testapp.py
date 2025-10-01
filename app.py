# app.py
def start_handler(msg):
bot.reply_to(msg, "Salom! Men Cal AI botman. Taom rasmini yuboring — men taxminiy kaloriyasini hisoblab beraman.\nAgar siz matn yozsangiz, masalan '200 g guruch', men ham hisoblay olaman.")




@bot.message_handler(content_types=['photo'])
def photo_handler(msg):
chat_id = msg.chat.id
bot.send_chat_action(chat_id, 'typing')
try:
file_info = bot.get_file(msg.photo[-1].file_id)
file_path = file_info.file_path
# yuklab olish
tmp = tempfile.NamedTemporaryFile(delete=False)
downloaded = bot.download_file(file_path)
tmp.write(downloaded)
tmp.flush()
tmp.seek(0)
img_bytes = tmp.read()
tmp.close()


# 1) Clarifai orqali aniqlash
concepts = identify_food_from_bytes(img_bytes, max_concepts=5)
if not concepts:
bot.reply_to(msg, "Kechirasiz, taomni aniqlay olmadim. Iltimos, boshqa rasm yuboring yoki taom nomini yozing.")
return


# tayyor javob: eng ehtimolli nom
primary_name, confidence = concepts[0]
# foydalanuvchiga topilganlar ro'yxatini jo'natish
labels = ', '.join([f"{n} ({round(conf*100,1)}%)" for n,conf in concepts])
bot.send_message(chat_id, f"Men bu rasmni quyidagicha topdim: {labels}\n\nEng ko'p ehtimol: {primary_name} ({round(confidence*100,1)}%)\n\nEndi kaloriyasini qidiryapman...")


# 2) Nutritionix orqali natural nutrients so'rovi (1 serving primary_name)
query_text = f"1 serving {primary_name}"
nut = get_nutrients_for_item_natural(query_text)
pretty = pretty_food_text(nut)
if not pretty:
bot.send_message(chat_id, f"Taom: {primary_name}\nAmmo Nutritionix orqali aniq nutrion topilmadi. Iltimos, taom nomini matn bilan yuboring (masalan: '200 g non').")
return
bot.send_message(chat_id, pretty)
bot.send_message(chat_id, "📌 Eslatma: bu taxminiy qiymat. Agar porsiyani aniq ko'rsatmoqchi bo'lsangiz, masalan: '200 g olma' deb yozing.")


except Exception as e:
logging.exception(e)
bot.reply_to(msg, f"Xatolik yuz berdi: {str(e)}")




@bot.message_handler(func=lambda m: True)
def text_handler(msg):
# agar foydalanuvchi matn yuborsa — to'g'ridan-to'g'ri natural nutrients bilan ishlaymiz
text = msg.text.strip()
try:
nut = get_nutrients_for_item_natural(text)
pretty = pretty_food_text(nut)
if pretty:
bot.reply_to(msg, pretty)
else:
bot.reply_to(msg, "Kechirasiz, bu so'rov bo'yicha ma'lumot topilmadi. Iltimos, quyidagi formatlarda yuboring:\n'1 serving rice' yoki '200 g chicken breast' yoki rasm yuboring.")
except Exception as e:
bot.reply_to(msg, f"Xatolik yuz berdi: {str(e)}")

if __name__ == '__main__':
print('Bot ishga tushdi...')
bot.infinity_polling()
