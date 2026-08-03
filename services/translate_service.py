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
        """Metindeki karakterlerden ve Türkçe kelimelerden sezgisel dil tahmini yapar."""
        tr_chars = set("çğıöşüÇĞİÖŞÜ")
        if any(c in tr_chars for c in text):
            return "tr"

        words = set(text.lower().split())
        tr_common_words = {
            "ve", "bir", "bu", "de", "da", "için", "ile", "ne", "var", "yok", "ama", "çok",
            "en", "her", "gibi", "kadar", "olan", "sonra", "önce", "tüm", "görseldeki", "görsel",
            "gibi", "görünüyor", "istiyorum", "yazının", "üstünün", "değişmesini", "tamam", "evet",
            "kaydet", "iptal", "basla", "baslaa", "seçim", "secim", "ekran", "cevir", "çevir",
            "metin", "orijinal", "etiketi", "kaldirildi", "kaldırıldı", "artik", "artık", "uzerinde",
            "üzerinde", "sadece", "cevrilen", "çevrilen", "hizli", "hızlı", "butonlari", "butonları"
        }
        if len(words.intersection(tr_common_words)) > 0:
            return "tr"

        # Türkçe ek kontrolleri (-ler, -lar, -dir, -dir, -den, -dan, -nin, -nin vb.)
        tr_suffixes = ("dir", "dır", "dur", "dür", "den", "dan", "ten", "tan", "ler", "lar", "nin", "nın", "nün", "nun", "yor", "ecek", "acak")
        tr_suffix_count = sum(1 for w in words if any(w.endswith(s) for s in tr_suffixes))
        if tr_suffix_count >= 2:
            return "tr"

        return "en"

    def _fetch_google(self, text: str, target_lang: str) -> tuple[str, str]:
        """Google Translate GTX uç noktasından çeviri ve algılanan kaynak dili alır."""
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q={quote(text)}"
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            translated_sentences = [item[0] for item in data[0] if item and item[0]]
            translated = "".join(translated_sentences)
            detected_src = ""
            if len(data) > 2 and data[2]:
                detected_src = str(data[2]).lower().split("-")[0]
            return translated, detected_src
        return "", ""

    def translate(self, text: str) -> tuple[str, str, str]:
        """
        Metni çevirir.
        Döndürür: (translated_text, source_lang, target_lang)
        Otomatik yön düzeltmesi: Eğer algılanan kaynak dil ile hedef dil aynı ise (örn: TR->TR),
        hedef dili otomatik olarak tersine çevirir (TR->EN).
        """
        if not text or not text.strip():
            return "", "auto", "tr"

        source_lang = self.detect_language(text)
        target_lang = "tr" if source_lang == "en" else "en"

        # 1. Hızlı Birincil Çeviri Servisi (Google Translate GTX)
        try:
            translated, detected_src = self._fetch_google(text, target_lang)
            if detected_src:
                source_lang = detected_src
                # Otomatik Yön Düzeltmesi: Kaynak Türkçe tespit edildiyse Hedef MUTLAKA İngilizce olmalı!
                if source_lang == "tr" and target_lang == "tr":
                    target_lang = "en"
                    translated, _ = self._fetch_google(text, "en")
                elif source_lang == "en" and target_lang == "en":
                    target_lang = "tr"
                    translated, _ = self._fetch_google(text, "tr")
                elif source_lang == "tr":
                    target_lang = "en"
                elif source_lang == "en":
                    target_lang = "tr"

            if translated:
                return translated, source_lang, target_lang
        except Exception as e:
            print(f"[ÇEVİRİ UYARISI] Google Translate hızlı servisi başarısız, yedek servisler deneniyor: {e}")

        # 2. Yedek Çeviri Servisi (LibreTranslate Sunucuları)
        for endpoint in self.libre_endpoints:
            try:
                payload = {
                    "q": text,
                    "source": "auto",
                    "target": target_lang,
                    "format": "text"
                }
                headers = {"Content-Type": "application/json"}
                response = requests.post(endpoint, json=payload, headers=headers, timeout=2)

                if response.status_code == 200:
                    data = response.json()
                    translated = data.get("translatedText", "")
                    if translated:
                        det = data.get("detectedLanguage", {})
                        if isinstance(det, dict) and "language" in det:
                            detected = str(det.get("language")).lower().split("-")[0]
                            if detected in ("en", "tr"):
                                source_lang = detected
                                target_lang = "tr" if source_lang == "en" else "en"
                        return translated, source_lang, target_lang
            except Exception:
                continue

        raise ConnectionError("İnternet bağlantısı bulunamadı veya çeviri sunucularına ulaşılamadı.")
