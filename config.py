import os

# BOT_TOKEN ni to'g'ridan-to'g'ri shu yerga yozing (os.getenv ni o'rniga)
BOT_TOKEN = "8054989710:AAHIM-fYa9ZMEz9OfPUQLb3qD0T4WRize18" 

# Whisper model - "base" yetarli, agar RAM kam bo'lsa "tiny" qiling
WHISPER_MODEL = "base"

# Vaqtinchalik fayllar papkasi
TEMP_DIR = "temp_files"
os.makedirs(TEMP_DIR, exist_ok=True)

# Video hajmini 1 GB (1024 MB) qilish
MAX_VIDEO_SIZE_MB = 1024

# FFmpeg yo'li
FFMPEG_PATH = "ffmpeg"
