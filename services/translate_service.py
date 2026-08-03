import requests
from urllib.parse import quote


class TranslationService:
    """
    LibreTranslate API'sini kullanarak OCR ile okunan metnin dilini otomatik tahmin eden,
    İngilizce ise Türkçeye, Türkçe ise İngilizceye çeviren servis.
    """
    def __init__(self):
        # Ücretsiz LibreTranslate kamuya açık uç noktaları
        self.libre_endpoints = [
            "https://libretranslate.de/translate",
            "https://translate.argosopentech.com/translate",
            "https://libretranslate.com/translate"
        ]

    def detect_language(self, text: str) -> str:
        """Metindeki karakterlerden sezgisel dil tahmini yapar."""
        tr_chars = set("çğıöşüÇĞİÖŞÜ")
        if any(c in tr_chars for c in text):
            return "tr"

        words = set(text.lower().split())
        tr_common_words = {"ve", "bir", "bu", "de", "da", "için", "ile", "ne", "var", "yok", "ama", "çok"}
        if len(words.intersection(tr_common_words)) > 0:
            return "tr"

        return "en"

    def translate(self, text: str) -> tuple[str, str, str]:
        """
        Metni çevirir.
        Döndürür: (translated_text, source_lang, target_lang)
        """
        if not text or not text.strip():
            return "", "auto", "tr"

        source_lang = self.detect_language(text)
        target_lang = "tr" if source_lang == "en" else "en"

        # 1. Ücretsiz LibreTranslate Sunucularını Dene (HTTP Timeout = 5sn)
        for endpoint in self.libre_endpoints:
            try:
                payload = {
                    "q": text,
                    "source": "auto",
                    "target": target_lang,
                    "format": "text"
                }
                headers = {"Content-Type": "application/json"}
                response = requests.post(endpoint, json=payload, headers=headers, timeout=5)

                if response.status_code == 200:
                    data = response.json()
                    translated = data.get("translatedText", "")
                    if translated:
                        det = data.get("detectedLanguage", {})
                        if isinstance(det, dict) and "language" in det:
                            detected = det.get("language")
                            if detected in ("en", "tr"):
                                source_lang = detected
                                target_lang = "tr" if source_lang == "en" else "en"
                        return translated, source_lang, target_lang
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                continue
            except Exception:
                continue

        # 2. Hızlı Yedek Çeviri Servisi (HTTP Timeout = 5sn)
        try:
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q={quote(text)}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                translated_sentences = [item[0] for item in data[0] if item and item[0]]
                translated = "".join(translated_sentences)
                if len(data) > 2 and data[2]:
                    detected = data[2]
                    if detected in ("en", "tr"):
                        source_lang = detected
                        target_lang = "tr" if source_lang == "en" else "en"
                return translated, source_lang, target_lang
        except requests.exceptions.RequestException:
            raise ConnectionError("İnternet bağlantısı kurulamadı. Lütfen ağ bağlantınızı ve internetinizi kontrol edin.")
        except Exception as e:
            raise RuntimeError(f"Çeviri servisi yanıt vermedi: {e}")

        raise ConnectionError("İnternet bağlantısı bulunamadı veya çeviri sunucularına ulaşılamadı.")
