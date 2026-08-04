import os
import sys
import unittest

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from services.privacy_service import PrivacyService


class TestPrivacyService(unittest.TestCase):

    def test_mask_api_key(self):
        privacy = PrivacyService(enabled=True)
        text = "My API key is sk-proj-1234567890abcdef1234567890 for testing."
        masked = privacy.mask_text(text)
        self.assertNotIn("sk-proj-1234567890abcdef1234567890", masked)
        self.assertIn("[REDACTED_KEY]", masked)

    def test_mask_email(self):
        privacy = PrivacyService(enabled=True)
        text = "Contact support@example.com for help."
        masked = privacy.mask_text(text)
        self.assertNotIn("support@example.com", masked)
        self.assertIn("[REDACTED_EMAIL]", masked)

    def test_mask_credit_card(self):
        privacy = PrivacyService(enabled=True)
        text = "Card number: 4532 1234 5678 9010 is invalid."
        masked = privacy.mask_text(text)
        self.assertNotIn("4532 1234 5678 9010", masked)
        self.assertIn("[REDACTED_CARD]", masked)

    def test_privacy_disabled(self):
        privacy = PrivacyService(enabled=False)
        text = "My API key is sk-proj-1234567890abcdef1234567890."
        masked = privacy.mask_text(text)
        self.assertEqual(masked, text)


if __name__ == "__main__":
    unittest.main()
