import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.context_engine import ContextEngine


class TestPhase1Features(unittest.TestCase):
    def setUp(self):
        self.engine = ContextEngine()

    def test_ai_summarize(self):
        text = "Python is an interpreted high-level programming language. It supports multiple programming paradigms. It has a large standard library."
        result = self.engine.process_ai_action("summarize", text)
        self.assertIn("Hızlı Özet", result)
        self.assertIn("•", result)

    def test_ai_explain_error(self):
        text = "AttributeError: 'NoneType' object has no attribute 'find_all'"
        result = self.engine.process_ai_action("explain_error", text)
        self.assertIn("Hata Analizi", result)
        self.assertIn("Eksik/Hatalı Öznitelik", result)
        self.assertIn("Çözüm Önerisi", result)

    def test_ai_draft_reply(self):
        text = "Please check the attached document and let me know your feedback by EOD."
        result = self.engine.process_ai_action("draft_reply", text)
        self.assertIn("Yanıt Taslakları", result)
        self.assertIn("Resmi / Profesyonel", result)


if __name__ == '__main__':
    unittest.main()
