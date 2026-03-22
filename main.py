from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CallbackQueryHandler, CommandHandler
import yt_dlp
import os

TOKEN = "8610455543:AAGsGr27LuyOo3w2oPsWdqiCEGz3Kn4Ed7I"

user_links = {}

# رسالة البداية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("اهلا 👋\nارسل الرابط ليتم التحميل 📥")

# استقبال الرابط
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    user_id = update.message.from_user.id
    user_links[user_id] = url

    await update.message.reply_text("⏳ جاري الفحص...")

    ydl_opts = {'quiet': True}

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    # فحص انستا
    if "instagram.com" in url:
        is_private = info.get("is_private", False)
        username = info.get("uploader", "غير معروف")
        fullname = info.get("title", "بدون اسم")

        if is_private:
            await update.message.reply_text(
                f"🔒 الحساب خاص\n\n👤 الاسم: {fullname}\n📛 اليوزر: {username}\n\n❌ لا يمكن التحميل من الحسابات الخاصة"
            )
            return

    formats = info.get('formats', [])

    buttons = []
    added = set()

    for f in formats:
        if f.get('height'):
            quality = f"{f['height']}p"
            if quality not in added:
                buttons.append([InlineKeyboardButton(quality, callback_data=f"video|{f['format_id']}")])
                added.add(quality)

    if not buttons:
        buttons.append([InlineKeyboardButton("📥 تحميل", callback_data="video_default")])

    buttons.append([InlineKeyboardButton("🎵 تحميل الصوت", callback_data="audio")])

    reply_markup = InlineKeyboardMarkup(buttons)

    await update.message.reply_text("اختر الجودة او النوع:", reply_markup=reply_markup)

# الضغط على الأزرار
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    url = user_links.get(user_id)

    await query.answer()
    await query.message.reply_text("⏳ جاري التحميل...")

    try:
        # صوت
        if data == "audio":
            ydl_opts = {
                'format': 'bestaudio',
                'outtmpl': 'audio.%(ext)s',
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            await query.message.reply_audio(audio=open(filename, "rb"))
            os.remove(filename)

        # فيديو مباشر (تيك توك / انستا)
        elif data == "video_default":
            ydl_opts = {
                'format': 'best',
                'outtmpl': 'video.%(ext)s',
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            if filename.endswith((".jpg", ".png")):
                await query.message.reply_photo(photo=open(filename, "rb"))
            else:
                await query.message.reply_video(video=open(filename, "rb"))

            os.remove(filename)

        # فيديو بجودة
        else:
            format_id = data.split("|")[1]

            ydl_opts = {
                'format': format_id,
                'outtmpl': 'video.%(ext)s',
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            await query.message.reply_video(video=open(filename, "rb"))
            os.remove(filename)

    except:
        await query.message.reply_text("❌ حدث خطأ اثناء التحميل")

# تشغيل البوت
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT, handle_message))
app.add_handler(CallbackQueryHandler(button_click))

print("البوت شغال 🔥")
app.run_polling()
