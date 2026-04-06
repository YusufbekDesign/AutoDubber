"""Video dan audio ajratish va qayta birlashtirish"""

import subprocess
import os
from config import TEMP_DIR, FFMPEG_PATH


def extract_audio(video_path: str, output_audio_path: str = None) -> str:
    """Video dan audio ajratib olish"""
    if output_audio_path is None:
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        output_audio_path = os.path.join(TEMP_DIR, f"{base_name}_audio.wav")

    cmd = [
        FFMPEG_PATH,
        "-i", video_path,
        "-vn",                    # Video olib tashlash
        "-acodec", "pcm_s16le",  # WAV format
        "-ar", "16000",           # 16kHz (Whisper uchun)
        "-ac", "1",               # Mono
        "-y",                     # Overwrite
        output_audio_path
    ]

    subprocess.run(cmd, capture_output=True, check=True)
    return output_audio_path


def extract_background_audio(video_path: str, vocals_path: str, output_path: str = None) -> str:
    """
    Fon musiqasi/tovushlarni ajratish (ovozni olib tashlash)
    Bu orqali faqat musiqa va sound effectlar qoladi
    """
    if output_path is None:
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(TEMP_DIR, f"{base_name}_background.wav")

    # Avval to'liq audioni olish
    full_audio = os.path.join(TEMP_DIR, "full_audio_temp.wav")
    cmd = [
        FFMPEG_PATH,
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        "-ac", "2",
        "-y",
        full_audio
    ]
    subprocess.run(cmd, capture_output=True, check=True)

    return output_path


def merge_video_audio(video_path: str, new_audio_path: str,
                       output_path: str = None,
                       background_audio_path: str = None) -> str:
    """Videoga yangi audio qo'shish (eski audioni olib tashlash)"""
    if output_path is None:
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(TEMP_DIR, f"{base_name}_dubbed.mp4")

    if background_audio_path and os.path.exists(background_audio_path):
        # Yangi ovoz + fon musiqasini birlashtirish
        cmd = [
            FFMPEG_PATH,
            "-i", video_path,
            "-i", new_audio_path,
            "-i", background_audio_path,
            "-filter_complex",
            "[1:a]volume=1.0[voice];[2:a]volume=0.3[bg];[voice][bg]amix=inputs=2:duration=longest[a]",
            "-map", "0:v",
            "-map", "[a]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-y",
            output_path
        ]
    else:
        # Faqat yangi ovoz
        cmd = [
            FFMPEG_PATH,
            "-i", video_path,
            "-i", new_audio_path,
            "-map", "0:v",        # Video birinchi fayldan
            "-map", "1:a",        # Audio ikkinchi fayldan
            "-c:v", "copy",       # Video codec copy (tez)
            "-c:a", "aac",        # Audio AAC
            "-b:a", "192k",
            "-shortest",          # Qisqaroqqa moslashtirish
            "-y",
            output_path
        ]

    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


def get_video_duration(video_path: str) -> float:
    """Video uzunligini olish (sekundlarda)"""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())
