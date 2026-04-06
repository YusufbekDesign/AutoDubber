"""Har qanday tildan O'zbek tiliga tarjima"""

import argostranslate.package
import argostranslate.translate
from typing import List
from speech_to_text import Segment


class Translator:
    def __init__(self):
        print("🔄 Tarjima modellari yuklanmoqda...")
        self._setup_argos()
        print("✅ Tarjima tayyor!")

    def _setup_argos(self):
        """Argos Translate paketlarini o'rnatish"""
        # Mavjud paketlarni yangilash
        argostranslate.package.update_package_index()
        available_packages = argostranslate.package.get_available_packages()

        # Kerakli til paketlarini o'rnatish
        # Argos Translate to'g'ridan-to'g'ri o'zbek tilini
        # qo'llab-quvvatlamasligi mumkin
        # Shuning uchun: Boshqa til → Inglizcha → O'zbekcha
        required_pairs = [
            ("ja", "en"),   # Yaponcha → Inglizcha
            ("ru", "en"),   # Ruscha → Inglizcha
            ("ko", "en"),   # Koreyscha → Inglizcha
            ("zh", "en"),   # Xitoycha → Inglizcha
            ("ar", "en"),   # Arabcha → Inglizcha
            ("fr", "en"),   # Fransuzcha → Inglizcha
            ("de", "en"),   # Nemischa → Inglizcha
            ("es", "en"),   # Ispancha → Inglizcha
        ]

        for from_code, to_code in required_pairs:
            try:
                pkg = next(
                    filter(
                        lambda x: x.from_code == from_code and x.to_code == to_code,
                        available_packages
                    ),
                    None
                )
                if pkg:
                    argostranslate.package.install_from_path(pkg.download())
                    print(f"  ✅ {from_code} → {to_code} o'rnatildi")
            except Exception as e:
                print(f"  ⚠️ {from_code} → {to_code} xato: {e}")

    def translate_to_uzbek(self, text: str, source_lang: str) -> str:
        """
        Har qanday tildan o'zbek tiliga tarjima

        Strategiya:
        1. Avval inglizchaga tarjima (Argos)
        2. Keyin inglizchadan o'zbekchaga (custom/Google)
        """
        if not text.strip():
            return ""

        try:
            # 1-qadam: Manba tildan inglizchaga
            if source_lang == "en":
                english_text = text
            else:
                english_text = argostranslate.translate.translate(
                    text, source_lang, "en"
                )

            # 2-qadam: Inglizchadan o'zbekchaga
            uzbek_text = self._english_to_uzbek(english_text)

            return uzbek_text

        except Exception as e:
            print(f"⚠️ Tarjima xatosi: {e}")
            # Fallback: to'g'ridan-to'g'ri qaytarish
            return text

    def _english_to_uzbek(self, english_text: str) -> str:
        """
        Inglizchadan o'zbekchaga tarjima

        Variant 1: Google Translate (bepul, cheklov bor)
        Variant 2: Helsinki-NLP modeli
        Variant 3: LibreTranslate
        """
        # === VARIANT 1: deep-translator (Google Translate wrapper) ===
        try:
            from deep_translator import GoogleTranslator
            result = GoogleTranslator(source='en', target='uz').translate(english_text)
            return result
        except ImportError:
            pass

        # === VARIANT 2: Helsinki-NLP (Hugging Face - offline) ===
        try:
            from transformers import MarianMTModel, MarianTokenizer

            model_name = "Helsinki-NLP/opus-mt-en-uz"
            tokenizer = MarianTokenizer.from_pretrained(model_name)
            model = MarianMTModel.from_pretrained(model_name)

            inputs = tokenizer(english_text, return_tensors="pt",
                             padding=True, truncation=True)
            translated = model.generate(**inputs)
            result = tokenizer.decode(translated[0], skip_special_tokens=True)
            return result
        except Exception:
            pass

        # === VARIANT 3: LibreTranslate API ===
        try:
            import requests
            response = requests.post(
                "https://libretranslate.de/translate",
                json={
                    "q": english_text,
                    "source": "en",
                    "target": "uz"
                },
                timeout=10
            )
            return response.json()["translatedText"]
        except Exception:
            pass

        return english_text  # Hech narsa ishlamasa inglizcha qaytarish

    def translate_segments(self, segments: List[Segment]) -> List[dict]:
        """Barcha segmentlarni tarjima qilish"""
        print("\n🌐 Tarjima qilinmoqda...")
        translated = []

        for i, seg in enumerate(segments):
            uzbek_text = self.translate_to_uzbek(seg.text, seg.language)
            print(f"  [{seg.language}] {seg.text}")
            print(f"  [uz]  {uzbek_text}")
            print()

            translated.append({
                "start": seg.start,
                "end": seg.end,
                "original_text": seg.text,
                "uzbek_text": uzbek_text,
                "speaker": seg.speaker,
                "language": seg.language
            })

        return translated
