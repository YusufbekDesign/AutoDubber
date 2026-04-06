"""Erkak va Ayol ovozini aniqlash"""

import numpy as np
import librosa
from typing import List
from speech_to_text import Segment


class VoiceGenderDetector:
    """
    Ovoz chastotasi (pitch) orqali erkak/ayolni aniqlash:
    - Erkak: ~85-180 Hz
    - Ayol: ~165-255 Hz
    """

    def __init__(self):
        self.male_pitch_range = (85, 180)
        self.female_pitch_range = (165, 300)

    def detect_gender(self, audio_path: str, start: float, end: float) -> str:
        """Berilgan vaqt oralig'idagi ovozning jinsini aniqlash"""
        try:
            # Audio ni yuklash
            y, sr = librosa.load(audio_path, sr=16000,
                                  offset=start, duration=end - start)

            if len(y) == 0:
                return "male"

            # Pitch (fundamental frequency) aniqlash
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)

            # Eng kuchli pitch larni olish
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 50:  # 50 Hz dan yuqori bo'lsa
                    pitch_values.append(pitch)

            if not pitch_values:
                return "male"

            avg_pitch = np.median(pitch_values)
            print(f"  🎵 O'rtacha pitch: {avg_pitch:.1f} Hz", end=" → ")

            if avg_pitch > 180:
                print("👧 Ayol")
                return "female"
            else:
                print("👦 Erkak")
                return "male"

        except Exception as e:
            print(f"  ⚠️ Gender aniqlashda xato: {e}")
            return "male"

    def assign_genders(self, audio_path: str,
                        segments: List[Segment]) -> List[Segment]:
        """Barcha segmentlarga gender belgilash"""
        print("\n🔍 Ovoz jinsini aniqlash...")
        for segment in segments:
            segment.speaker = self.detect_gender(
                audio_path, segment.start, segment.end
            )
        return segments
