import os
import sys
import unittest

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from services.privacy_service import PrivacyService
from services.translate_service import TranslationService


class TestTranslationService(unittest.TestCase):

    def test_clean_text(self):
        service = TranslationService()
        text = "This is a line.\n\nThis is another paragraph\nwith broken lines."
        cleaned = service.clean_text(text)
        self.assertIn("with broken lines", cleaned)
        self.assertIn("\n\n", cleaned)

    def test_detect_language_turkish(self):
        service = TranslationService()
        text = "Bu bir Türkçe metin örneğidir ve çeviri yapılmalıdır."
        lang = service.detect_language(text)
        self.assertEqual(lang, "tr")

    def test_detect_language_english(self):
        service = TranslationService()
        text = "This is an english sentence for automatic language detection."
        lang = service.detect_language(text)
        self.assertEqual(lang, "en")

    def test_privacy_integration_in_translate(self):
        privacy = PrivacyService(enabled=True)
        service = TranslationService(privacy_service=privacy)

        input_text = "Here is secret token sk-proj-1234567890abcdef1234567890"
        try:
            translated, src, tgt = service.translate(input_text)
            self.assertNotIn("sk-proj-1234567890abcdef1234567890", translated)
        except ConnectionError:
            pass


if __name__ == "__main__":
    unittest.main()
