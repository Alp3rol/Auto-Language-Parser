import sys
import os
import unittest
from PIL import Image
from PySide6.QtCore import QRect
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.image_analysis import extract_dominant_bg_color, get_contrast_text_color
from ui.in_place_overlay import InPlaceOverlay


class TestInPlaceOverlay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def test_dominant_bg_color_extraction(self):
        # Siyah test görseli
        img_black = Image.new("RGB", (100, 100), color=(10, 10, 10))
        bg_black = extract_dominant_bg_color(img_black)
        self.assertEqual(bg_black.red(), 10)

        # Beyaz zıt renk testi
        contrast = get_contrast_text_color(bg_black)
        self.assertEqual(contrast.red(), 248)  # Açık renk metin seçilmeli

    def test_in_place_overlay_initialization(self):
        rect = QRect(100, 100, 300, 150)
        img = Image.new("RGB", (300, 150), color=(20, 20, 20))
        overlay = InPlaceOverlay(rect, "Lorem Ipsum Türkçe Çevirisi", pil_image=img)
        self.assertIsNotNone(overlay)
        self.assertGreater(overlay.font_size, 8)
        overlay.close()


if __name__ == '__main__':
    unittest.main()
