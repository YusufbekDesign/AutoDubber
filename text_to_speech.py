"""O'zbekcha Text-to-Speech - Realistic ovozlar"""

import subprocess
import os
import wave
import struct
import numpy as np
from typing import List
from config import TEMP_DIR


class UzbekTTS:
    """
    O'zbek tilida ovoz sintezi

    Variantlar:
    1. Piper TTS - eng yaxshi offline variant
    2. Edge TTS - Microsoft (bepul, online)
    3. gTTS - Google TTS
    """

    def __init__(self, method="edge"):
        """
        method: "piper", "edge", "gtts"
        """
        self.method = method
        print(f"🔊 TTS method: {method}")

    async def synthesize(self, text: str, gender: str,
                          output_path: str) -> str:
        """Matnni ovozga aylantirish"""
        if self.method == "edge":
            return await self._edge_tts(text, gender, output_path)
        elif self.method == "piper":
            return self._piper_tts(text, gender, output_path)
        elif self.method == "gtts":
            return self._gtts_tts(text, gender, output_path)

    async def _edge_tts(self, text: str, gender: str,
                         output_path: str) -> str:
        """
        Microsoft Edge TTS - Eng yaxshi bepul variant!
        Juda realistic ovozlar
        """
        import edge_tts

        # O'zbek ovozlari
        voices = {
            "male": "uz-UZ-SardorNeural",     # Erkak ovoz
            "female": "uz-UZ-MadinaNeural"     # Ayol ovoz
        }

        voice = voices.get(gender, voices["male"])

        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)

        print(f"  🔈 TTS [{gender}]: {text[:50]}...")
        return output_path

    def _piper_tts(self, text: str, gender: str, output_path: str) -> str:
        """
        Piper TTS - Offline, tez, yaxshi sifat
        Modelni oldindan yuklab olish kerak
        """
        model_path = f"piper_models/uz_UZ-{gender}-medium.onnx"

        if not os.path.exists(model_path):
            print(f"  ⚠️ Piper model topilmadi: {model_path}")
            return None

        cmd = [
            "piper",
            "--model", model_path,
            "--output_file", output_path
        ]

        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            capture_output=True
        )
        process.communicate(input=text.encode("utf-8"))
        return output_path

    def _gtts_tts(self, text: str, gender: str, output_path: str) -> str:
        """Google TTS - Oddiy lekin ishlaydi"""
        from gtts import gTTS

        # gTTS da gender tanlash imkoni cheklangan
        tts = gTTS(text=text, lang='uz')
        tts.save(output_path)
        return output_path

    async def generate_full_audio(self, translated_segments: List[dict],
                                    total_duration: float) -> str:
        """
        Barcha segmentlardan bitta audio fayl yaratish
        Har bir segment o'z vaqtida joylashadi
        """
        print("\n🎙️ O'zbekcha audio generatsiya qilinmoqda...")

        segment_files = []

        for i, seg in enumerate(translated_segments):
            seg_output = os.path.join(TEMP_DIR, f"tts_segment_{i}.wav")

            await self.synthesize(
                text=seg["uzbek_text"],
                gender=seg["speaker"],
                output_path=seg_output
            )

            if os.path.exists(seg_output):
                segment_files.append({
                    "file": seg_output,
                    "start": seg["start"],
                    "end": seg["end"]
                })

        # Barcha segmentlarni bitta audio ga birlashtirish
        output_path = os.path.join(TEMP_DIR, "final_uzbek_audio.wav")
        self._merge_segments_with_timing(
            segment_files, output_path, total_duration
        )

        return output_path

    def _merge_segments_with_timing(self, segments: list,
                                      output_path: str,
                                      total_duration: float):
        """
        Segmentlarni to'g'ri vaqtlarda joylashtirish

        Masalan:
        - 0-2s: Jim (sukunat)
        - 2-5s: "Salom, qalaysiz?"
        - 5-7s: Jim
        - 7-10s: "Men yaxshiman"
        """
        from pydub import AudioSegment

        # Bo'sh audio yaratish (total_duration uzunligida)
        total_ms = int(total_duration * 1000)
        final_audio = AudioSegment.silent(duration=total_ms)

        for seg in segments:
            if not os.path.exists(seg["file"]):
                continue

            # Segment audiosini yuklash
            seg_audio = AudioSegment.from_wav(seg["file"])

            # Segment uzunligini tekshirish
            available_duration = (seg["end"] - seg["start"]) * 1000
            if len(seg_audio) > available_duration:
                # Tezlashtirish kerak bo'lsa
                speed_factor = len(seg_audio) / available_duration
                if speed_factor < 2.0:  # 2x dan ko'p tezlashtirmaslik
                    seg_audio = self._speed_up(seg_audio, speed_factor)

            # To'g'ri vaqtga joylashtirish
            start_ms = int(seg["start"] * 1000)
            final_audio = final_audio.overlay(seg_audio, position=start_ms)

        # Saqlash
        final_audio.export(output_path, format="wav")
        print(f"✅ Yakuniy audio: {output_path}")

    def _speed_up(self, audio: 'AudioSegment', factor: float) -> 'AudioSegment':
        """Audioni tezlashtirish"""
        from pydub.effects import speedup
        try:
            return speedup(audio, playback_speed=factor)
        except Exception:
            return audio
