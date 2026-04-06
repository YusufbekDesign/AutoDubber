"""
Auto Dubber Telegram Bot
Har qanday tildagi videoni o'zbek tiliga dublyaj qiladi
"""

import os
import asyncio
import time
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)

from config import BOT_TOKEN, TEMP_DIR, MAX_VIDEO_SIZE_MB
from audio_extractor import extract_audio, merge_video_audio, get_video_duration
from speech_to_text import SpeechToText
from voice_detector import VoiceGenderDetector
from translator import Translator
from text_to_speech import UzbekTTS

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global obyektlar
stt = None
translator = None
tts = None
gender_detector = None


async def initialize():
    """Modellarni yuklash"""
    global stt, translator, tts, gender_detector
    stt = SpeechToText()
    translator = Translator()
    tts = UzbekTTS(method="edge")
    gender_detector = VoiceGenderDetector()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot ishga tushganda"""
    welcome_text = """
🎬 **Auto Dubber Bot** ga xush kelibsiz!

Men har qanday tildagi videoni **O'zbek tiliga** dublyaj qilaman!

🌍 **Qo'llab-quvvatlanadigan tillar:**
🇯🇵 Yaponcha (Anime)
🇷🇺 Ruscha
🇺🇸 Inglizcha
🇰🇷 Koreyscha
🇨🇳 Xitoycha
🇫🇷 Fransuzcha
🇩🇪 Nemischa
va yana 90+ til!

📹 **Foydalanish:**
Menga video yuboring - men uni o'zbekcha dublyaj qilib qaytaraman!

⚡ **Imkoniyatlar:**
✅ Erkak va Ayol ovozlarini ajratish
✅ Realistic o'zbek ovozi
✅ Asl ovozni to'liq almashtirish
✅ Vaqt sinxronizatsiyasi

📌 Video yuboring va kuting!
    """

    keyboard = [
        [InlineKeyboardButton("ℹ️ Yordam", callback_data="help")],
        [InlineKeyboardButton("⚙️ Sozlamalar", callback_data="settings")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Video kelganda ishlov berish"""
    message = update.message

    # Video borligini tekshirish
    video = message.video or message.document
    if not video:
        await message.reply_text("❌ Video yuborilmadi!")
        return

    # Hajmni tekshirish
    file_size_mb = video.file_size / (1024 * 1024)
    if file_size_mb > MAX_VIDEO_SIZE_MB:
        await message.reply_text(
            f"❌ Video juda katta! Maksimum: {MAX_VIDEO_SIZE_MB}MB\n"
            f"Sizniki: {file_size_mb:.1f}MB"
        )
        return

    # Jarayon boshlash
    status_msg = await message.reply_text(
        "🔄 **Video qabul qilindi!**\n\n"
        "📥 Yuklab olinmoqda...",
        parse_mode="Markdown"
    )

    start_time = time.time()

    try:
        # === 1-QADAM: Video yuklab olish ===
        await status_msg.edit_text(
            "📥 **1/6** Video yuklab olinmoqda..."
        )
        file = await video.get_file()
        video_path = os.path.join(TEMP_DIR, f"{message.message_id}_input.mp4")
        await file.download_to_drive(video_path)

        # Video uzunligini olish
        duration = get_video_duration(video_path)
        print(f"📹 Video uzunligi: {duration:.1f} sekund")

        # === 2-QADAM: Audio ajratish ===
        await status_msg.edit_text(
            "🔊 **2/6** Audio ajratilmoqda..."
        )
        audio_path = extract_audio(video_path)

        # === 3-QADAM: Speech-to-Text ===
        await status_msg.edit_text(
            "🗣️ **3/6** Ovoz tanilmoqda...\n"
            "_(Har qanday tilda tushunaman)_",
            parse_mode="Markdown"
        )
        segments = stt.transcribe(audio_path)

        if not segments:
            await status_msg.edit_text(
                "❌ Videoda ovoz topilmadi! Iltimos, gapirish bor videoni yuboring."
            )
            return

        # === 4-QADAM: Gender aniqlash ===
        await status_msg.edit_text(
            "🔍 **4/6** Erkak/Ayol ovozi aniqlanmoqda..."
        )
        segments = gender_detector.assign_genders(audio_path, segments)

        # === 5-QADAM: Tarjima ===
        await status_msg.edit_text(
            f"🌐 **5/6** O'zbek tiliga tarjima qilinmoqda...\n"
            f"_{segments[0].language} → uz_",
            parse_mode="Markdown"
        )
        translated = translator.translate_segments(segments)

        # === 6-QADAM: TTS + Video birlashtirish ===
        await status_msg.edit_text(
            "🎙️ **6/6** O'zbekcha ovoz generatsiya qilinmoqda...\n"
            "🎬 Video tayyorlanmoqda..."
        )

        # TTS
        uzbek_audio_path = await tts.generate_full_audio(
            translated, duration
        )

        # Video + yangi audio
        output_video_path = merge_video_audio(video_path, uzbek_audio_path)

        # === NATIJA ===
        elapsed = time.time() - start_time

        # Statistika
        stats_text = (
            f"✅ **Dublyaj tayyor!**\n\n"
            f"🌐 Asl til: `{segments[0].language}`\n"
            f"📝 Segmentlar: {len(segments)} ta\n"
            f"👦 Erkak ovozlar: {sum(1 for s in translated if s['speaker'] == 'male')}\n"
            f"👧 Ayol ovozlar: {sum(1 for s in translated if s['speaker'] == 'female')}\n"
            f"⏱️ Vaqt: {elapsed:.0f} sekund\n"
        )

        await status_msg.edit_text(stats_text, parse_mode="Markdown")

        # Video yuborish
        with open(output_video_path, "rb") as f:
            await message.reply_video(
                video=f,
                caption="🎬 O'zbekcha dublyaj | Auto Dubber Bot",
                supports_streaming=True
            )

    except Exception as e:
        logger.error(f"Xato: {e}", exc_info=True)
        await status_msg.edit_text(
            f"❌ **Xatolik yuz berdi!**\n\n"
            f"`{str(e)[:200]}`\n\n"
            f"Iltimos, qayta urinib ko'ring.",
            parse_mode="Markdown"
        )

    finally:
        # Vaqtinchalik fayllarni tozalash
        cleanup_temp_files(message.message_id)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tugmalar callback"""
    query = update.callback_query
    await query.answer()

    if query.data == "help":
        help_text = """
ℹ️ **Yordam**

**Qanday ishlaydi?**
1. Videoni menga yuboring
2. Men videodagi ovozni taniyman
3. O'zbek tiliga tarjima qilaman
4. Erkak/Ayol ovozida qayta gaplashaman
5. Tayyor videoni qaytaraman

**Eslatmalar:**
• Musiqa va qo'shiqlar tarjima qilinmaydi
• Video max 50MB bo'lishi kerak
• Sifatli audio bo'lsa yaxshiroq natija
        """
        await query.edit_message_text(help_text, parse_mode="Markdown")

    elif query.data == "settings":
        keyboard = [
            [InlineKeyboardButton("🔈 Ovoz sifati: Yuqori",
                                   callback_data="quality_high")],
            [InlineKeyboardButton("🔙 Orqaga", callback_data="back")]
        ]
        await query.edit_message_text(
            "⚙️ **Sozlamalar**",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


def cleanup_temp_files(message_id: int):
    """Vaqtinchalik fayllarni o'chirish"""
    for f in os.listdir(TEMP_DIR):
        if str(message_id) in f or f.startswith("tts_segment_"):
            try:
                os.remove(os.path.join(TEMP_DIR, f))
            except Exception:
                pass


def main():
    """Botni ishga tushirish"""
    print("🤖 Auto Dubber Bot ishga tushmoqda...")

    # Application yaratish
    app = Application.builder().token(BOT_TOKEN).build()

    # Modellarni yuklash
    loop = asyncio.get_event_loop()
    loop.run_until_complete(initialize())

    # Handlerlar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO,
                                    handle_video))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print("✅ Bot tayyor! Ishlayapti...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
