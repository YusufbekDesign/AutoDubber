import os

# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Whisper model - "tiny", "base", "small", "medium", "large"
# "base" - tez va yetarlicha aniq
# "large" - eng aniq lekin sekin
WHISPER_MODEL = "base"

# Piper TTS o'zbek ovoz modellari
# GitHub dan yuklab olish kerak
PIPER_VOICES = {
    "male": "uz_UZ-male-medium.onnx",
    "female": "uz_UZ-female-medium.onnx"
}

# Vaqtinchalik fayllar papkasi
TEMP_DIR = "temp_files"
os.makedirs(TEMP_DIR, exist_ok=True)

# Maksimal video hajmi (MB)
MAX_VIDEO_SIZE_MB = 50

# FFmpeg yo'li
FFMPEG_PATH = "ffmpeg"
