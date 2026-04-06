FROM python:3.10-slim

# FFmpeg va kerakli narsalarni o'rnatish
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Ishchi papka yaratish
WORKDIR /app

# Requirements faylni ko'chirish
COPY requirements.txt .

# Python kutubxonalarni o'rnatish
RUN pip install --no-cache-dir -r requirements.txt

# Barcha kodni ko'chirish
COPY . .

# Temp papka yaratish
RUN mkdir -p temp_files

# Botni ishga tushirish
CMD ["python", "bot.py"]
