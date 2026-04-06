"""Ovozni matnga o'girish - Har qanday tilni tushunadi"""

from faster_whisper import WhisperModel
from config import WHISPER_MODEL
from dataclasses import dataclass
from typing import List


@dataclass
class Segment:
    """Bitta gap segmenti"""
    start: float      # Boshlanish vaqti (sekund)
    end: float         # Tugash vaqti (sekund)
    text: str          # Matn
    language: str      # Aniqlangan til
    speaker: str       # "male" yoki "female" (keyinroq aniqlanadi)


class SpeechToText:
    def __init__(self):
        print("🔄 Whisper model yuklanmoqda...")
        # device: "cpu" yoki "cuda" (GPU)
        # compute_type: "int8" (tez), "float16" (GPU), "float32" (aniq)
        self.model = WhisperModel(
            WHISPER_MODEL,
            device="cpu",
            compute_type="int8"
        )
        print("✅ Whisper model tayyor!")

    def transcribe(self, audio_path: str) -> List[Segment]:
        """
        Audio faylni matnga o'girish

        HAR QANDAY TILDA ishlaydi:
        - Yaponcha (anime)
        - Ruscha
        - Inglizcha
        - Koreyscha
        - Xitoycha
        - va boshqa 90+ til
        """
        segments_result, info = self.model.transcribe(
            audio_path,
            beam_size=5,
            word_timestamps=True,
            vad_filter=True,          # Voice Activity Detection
            vad_parameters=dict(
                min_silence_duration_ms=500,
                speech_pad_ms=200
            )
        )

        detected_language = info.language
        print(f"🌐 Aniqlangan til: {detected_language} "
              f"(ishonch: {info.language_probability:.2f})")

        segments = []
        for seg in segments_result:
            segment = Segment(
                start=seg.start,
                end=seg.end,
                text=seg.text.strip(),
                language=detected_language,
                speaker="unknown"  # Keyinroq aniqlanadi
            )
            segments.append(segment)
            print(f"  [{seg.start:.1f}s - {seg.end:.1f}s] {seg.text}")

        return segments

    def detect_language(self, audio_path: str) -> str:
        """Faqat tilni aniqlash"""
        _, info = self.model.transcribe(audio_path, beam_size=1)
        return info.language
