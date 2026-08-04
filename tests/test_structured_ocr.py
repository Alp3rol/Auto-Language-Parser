import sys
import os
import unittest
from PIL import Image, ImageDraw, ImageFont
from PySide6.QtCore import QRect
from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.ocr_service import OCRService
from services.translate_service import TranslationService
from ui.in_place_overlay import InPlaceOverlay


class TestStructuredOCRAndOverlay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def test_extract_structured_blocks(self):
        # Sentetik başlık ve paragraf içeren test görseli oluştur
        img = Image.new("RGB", (500, 200), color=(20, 20, 20))
        draw = ImageDraw.Draw(img)
        # Başlık
        draw.text((20, 20), "WHAT IS LOREM IPSUM?", fill=(255, 255, 255))
        # Paragraf
        draw.text((20, 80), "Lorem Ipsum is simply dummy text of the printing industry.", fill=(220, 220, 220))

        ocr = OCRService()
        blocks = ocr.extract_structured_blocks(img)

        self.assertIsInstance(blocks, list)
        self.assertGreater(len(blocks), 0)

        # En az bir bloğun x, y, w, h ve text içerdiğini doğrula
        first = blocks[0]
        self.assertIn("x", first)
        self.assertIn("y", first)
        self.assertIn("w", first)
        self.assertIn("h", first)
        self.assertIn("text", first)

    def test_in_place_overlay_with_structured_blocks(self):
        rect = QRect(100, 100, 400, 200)
        blocks = [
            {"x": 10, "y": 10, "w": 250, "h": 30, "text": "WHAT IS LOREM IPSUM?", "translated_text": "LOREM IPSUM NEDİR?", "line_height": 30, "is_heading": True, "is_bold": True},
            {"x": 10, "y": 60, "w": 350, "h": 16, "text": "Lorem Ipsum is simply...", "translated_text": "Lorem Ipsum matbaacılık ve dizgi...", "line_height": 16, "is_heading": False, "is_bold": False}
        ]
        overlay = InPlaceOverlay(rect, structured_blocks=blocks)
        self.assertIsNotNone(overlay)
        self.assertEqual(len(overlay.structured_blocks), 2)
        self.assertTrue(overlay.structured_blocks[0]["is_heading"])
        overlay.close()


if __name__ == '__main__':
    unittest.main()
