import os
import sys
import tempfile
import unittest

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from services.anki_export_service import AnkiExportService


class TestAnkiExportService(unittest.TestCase):

    def test_export_to_tsv(self):
        cards = [
            {"word": "deprecated", "translation": "kullanımdan kaldırılmış"},
            {"word": "refactor", "translation": "kodu yeniden yapılandır"},
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = os.path.join(tmp_dir, "anki_deck.txt")
            success = AnkiExportService.export_to_tsv(cards, output_file)

            self.assertTrue(success)
            self.assertTrue(os.path.exists(output_file))

            with open(output_file, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("#separator:tab", content)
            self.assertIn("deprecated\tkullanımdan kaldırılmış", content)
            self.assertIn("refactor\tkodu yeniden yapılandır", content)


if __name__ == "__main__":
    unittest.main()
