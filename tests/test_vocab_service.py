import os
import sys
import tempfile
import unittest

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from services.vocab_service import VocabService


class TestVocabService(unittest.TestCase):

    def test_vocab_service_crud_and_sm2(self):
        # Use temp dir with ignore_cleanup_errors=True for Windows file lock compatibility
        tmp_dir = tempfile.mkdtemp()
        db_path = os.path.join(tmp_dir, "test_vocab.db")
        try:
            service = VocabService(db_path=db_path)

            # 1. Add Word
            added = service.add_word(
                "deprecated", "kullanımdan kaldırılmış", "en", "tr"
            )
            self.assertTrue(added)

            # 2. Get All Words
            all_words = service.get_all_words()
            self.assertEqual(len(all_words), 1)
            self.assertEqual(all_words[0]["word"], "deprecated")

            # 3. Due Cards
            due_cards = service.get_due_cards()
            self.assertEqual(len(due_cards), 1)

            # 4. Review Card (Quality = 5 Easy)
            card_id = due_cards[0]["id"]
            service.review_card(card_id, quality=5)

            updated_words = service.get_all_words()
            self.assertEqual(updated_words[0]["repetition_count"], 1)
            self.assertEqual(updated_words[0]["interval_days"], 1)

            # 5. Delete Word
            service.delete_word(card_id)
            self.assertEqual(len(service.get_all_words()), 0)
        finally:
            try:
                import shutil
                shutil.rmtree(tmp_dir, ignore_errors=True)
            except Exception:
                pass


if __name__ == "__main__":
    unittest.main()
