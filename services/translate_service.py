import requests
from urllib.parse import quote


from services.privacy_service import PrivacyService


class TranslationService:
    """
    LibreTranslate API'sini kullanarak OCR ile okunan metnin dilini otomatik tahmin eden,
    İngilizce ise Türkçeye, Türkçe ise İngilizceye çeviren servis.
    """
    SUPPORTED_LANGUAGES = {
        "tr": "Türkçe 🇹🇷",
        "en": "İngilizce 🇬🇧",
        "de": "Almanca 🇩🇪",
        "fr": "Fransızca 🇫🇷",
        "es": "İspanyolca 🇪🇸",
        "it": "İtalyanca 🇮🇹",
        "ru": "Rusça 🇷🇺",
        "ja": "Japonca 🇯🇵",
        "ko": "Korece 🇰🇷",
        "zh": "Çince 🇨🇳",
        "ar": "Arapça 🇸🇦",
        "pt": "Portekizce 🇵🇹",
        "nl": "Hollandaca 🇳🇱",
        "pl": "Lehçe 🇵🇱",
        "sv": "İsveççe 🇸🇪",
        "uk": "Ukraynaca 🇺🇦",
        "el": "Yunanaca 🇬🇷",
        "hi": "Hintçe 🇮🇳"
    }

    def __init__(self, privacy_service: PrivacyService = None):
        # Ücretsiz LibreTranslate kamuya açık uç noktaları
        self.libre_endpoints = [
            "https://libretranslate.de/translate",
            "https://translate.argosopentech.com/translate",
            "https://libretranslate.com/translate"
        ]
        self.privacy_service = privacy_service or PrivacyService()

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

    def clean_text(self, text: str) -> str:
        """
        OCR'dan gelen yapay satır sonu (\n) kırılmalarını temizleyerek cümlelerin bölünmesini önler.
        Google Translate'in cümle bütünlüğünü koruyup kurallı Türkçe (özne-yüklem uyumlu) çeviri yapmasını sağlar.
        """
        if not text or not text.strip():
            return ""
        paragraphs = text.split("\n\n")
        cleaned_paragraphs = []
        for p in paragraphs:
            lines = [line.strip() for line in p.splitlines() if line.strip()]
            cleaned_p = " ".join(lines)
            if cleaned_p:
                cleaned_paragraphs.append(cleaned_p)
        return "\n\n".join(cleaned_paragraphs)

    def translate(self, text: str, target_lang: str = "tr", auto_detect: bool = True) -> tuple[str, str, str]:
        """
        Metni çevirir.
        Döndürür: (translated_text, source_lang, target_lang)
        """
        if not text or not text.strip():
            return "", "auto", target_lang or "tr"

        # Privacy Shield: Dış sunucuya gönderilmeden önce metindeki hassas bilgileri (API key, email vs.) maskele
        text = self.privacy_service.mask_text(text)

        # OCR yapay satır kırılmalarını temizleyerek Google Translate'e tek bütün cümle olarak gönder
        text = self.clean_text(text)


        source_lang = self.detect_language(text)

        if auto_detect:
            # Otomatik Yön Düzeltmesi: Kaynak EN ise TR'ye, TR ise EN'e çevir, farklı dildeyse seçili hedef dile çevir.
            if source_lang == "en" and target_lang == "en":
                target_lang = "tr"
            elif source_lang == "tr" and target_lang == "tr":
                target_lang = "en"

        # 1. Hızlı Birincil Çeviri Servisi (Google Translate GTX)
        try:
            translated, detected_src = self._fetch_google(text, target_lang)
            if detected_src:
                source_lang = detected_src
                if auto_detect:
                    if source_lang == "tr" and target_lang == "tr":
                        target_lang = "en"
                        translated, _ = self._fetch_google(text, "en")
                    elif source_lang == "en" and target_lang == "en":
                        target_lang = "tr"
                        translated, _ = self._fetch_google(text, "tr")

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
                            if detected:
                                source_lang = detected
                        return translated, source_lang, target_lang
            except Exception:
                continue

        raise ConnectionError("İnternet bağlantısı bulunamadı veya çeviri sunucularına ulaşılamadı.")
