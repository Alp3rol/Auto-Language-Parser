import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.ocr_service import OCRService
from PIL import Image, ImageDraw


class TestPhase2Features(unittest.TestCase):
    def setUp(self):
        self.ocr_service = OCRService()

    def test_winocr_availability(self):
        # WinOCR kütüphanesinin ve sistem dil paketinin durumunu sına
        is_avail = self.ocr_service.is_winocr_available()
        print(f"[TEST INFO] WinOCR Available: {is_avail}")
        self.assertIsInstance(is_avail, bool)

    def test_winocr_extraction(self):
        img = Image.new("RGB", (250, 60), color="white")
        draw = ImageDraw.Draw(img)
        draw.text((10, 15), "TEST WINOCR PARSER", fill="black")

        # WinOCR motoru ile dene
        res_win = self.ocr_service.extract_text(img, engine="winocr")
        # Auto mod ile dene
        res_auto = self.ocr_service.extract_text(img, engine="auto")

        self.assertIsInstance(res_win, str)
        self.assertIsInstance(res_auto, str)


if __name__ == '__main__':
    unittest.main()
