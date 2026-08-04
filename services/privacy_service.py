import re


class PrivacyService:
    """
    Ekran OCR veya panodan alınan metinlerdeki hassas kişisel/güvenlik verilerini (API Key, Email, Şifre, Kredi Kartı)
    dış çeviri servislerine gönderilmeden önce tespit edip maskeleyen güvenlik servisi (Privacy Shield).
    """

    # Hassas Veri Regex Desenleri
    PATTERNS = {
        "api_key": r"(?i)\b(sk-[a-zA-Z0-9_\-]{20,}|AKIA[0-9A-Z]{16}|ghp_[a-zA-Z0-9]{36}|bearer\s+[a-zA-Z0-9\-\._~\+\/]+=*)\b",
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "credit_card": r"\b(?:\d[ -]*?){13,16}\b",
        "tc_kn": r"\b[1-9][0-9]{10}\b",
        "jwt_token": r"\beyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*\b",
    }

    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    def mask_text(self, text: str) -> str:
        """
        Metin içerisindeki tüm hassas bilgileri güvenli placeholder'lar ile değiştirir.
        """
        if not self.enabled or not text:
            return text

        masked_text = text

        # 1. API Key / Token Maskeleme
        masked_text = re.sub(self.PATTERNS["api_key"], "[REDACTED_KEY]", masked_text)

        # 2. JWT Token Maskeleme
        masked_text = re.sub(self.PATTERNS["jwt_token"], "[REDACTED_TOKEN]", masked_text)

        # 3. Email Maskeleme
        masked_text = re.sub(self.PATTERNS["email"], "[REDACTED_EMAIL]", masked_text)

        # 4. Kredi Kartı Maskeleme (13-16 haneli sayılar)
        def _mask_card(match):
            digits = re.sub(r"\D", "", match.group(0))
            if 13 <= len(digits) <= 16:
                return "[REDACTED_CARD]"
            return match.group(0)

        masked_text = re.sub(self.PATTERNS["credit_card"], _mask_card, masked_text)

        return masked_text
