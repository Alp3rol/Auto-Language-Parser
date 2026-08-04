import sys
import os


class ContextEngine:
    """
    Ekrandaki metni ve aktif uygulamayı inceleyerek bağlamı (Software, Gaming, Legal, Manga) algılayan ve
    jargona özel çeviri uyarlaması yapan akıllı zeka motoru.
    """
    SOFTWARE_TERMS = {
        "deprecated": "kullanımdan kaldırıldı (ömrü doldu)",
        "refactor": "kodu yeniden yapılandır",
        "override": "üzerine yaz (ezme)",
        "callback": "geri çağırma fonksiyonu",
        "thread": "iş parçacığı",
        "buffer": "arabellek",
        "pipeline": "işlem hattı",
        "array": "dizi",
        "stack trace": "hata izleme yığını",
        "repository": "kod deposu (repo)",
        "instance": "örnek / nesne örneği"
    }

    GAMING_TERMS = {
        "deprecated": "eski / kullanılmayan eşya",
        "buff": "güçlendirme",
        "debuff": "zayıflatma",
        "cooldown": "bekleme süresi",
        "quest": "görev",
        "inventory": "envanter",
        "durability": "dayanıklılık",
        "loot": "ganimet"
    }

    def detect_context(self, text: str) -> str:
        """
        Metindeki anahtar kelimelere göre alanı tespit eder: 'software', 'gaming', 'general'
        """
        text_lower = text.lower()

        sw_score = sum(1 for k in self.SOFTWARE_TERMS if k in text_lower)
        game_score = sum(1 for k in self.GAMING_TERMS if k in text_lower)

        if sw_score > game_score and sw_score >= 1:
            return "software"
        elif game_score > sw_score and game_score >= 1:
            return "gaming"

        return "general"

    def adapt_translation(self, original_text: str, default_translated: str) -> str:
        """
        Çeviriyi algılanan jargona göre zenginleştirir ve düzeltir.
        """
        context = self.detect_context(original_text)
        text_lower = original_text.lower().strip()

        if context == "software":
            for term, replacement in self.SOFTWARE_TERMS.items():
                if term in text_lower:
                    # Tek kelimelik eşleşmede doğrudan jargon karşılığını kullan
                    if text_lower in (term, f"({term})", f"[{term}]"):
                        return replacement.capitalize()
        elif context == "gaming":
            for term, replacement in self.GAMING_TERMS.items():
                if term in text_lower:
                    if text_lower in (term, f"({term})", f"[{term}]"):
                        return replacement.capitalize()

        return default_translated
