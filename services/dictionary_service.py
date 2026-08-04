import requests
from urllib.parse import quote


class DictionaryService:
    """
    Kelimelerin okunuşunu (fonetik), Türkçe anlamlarını, gramer türünü ve örnek cümle kullanımını sağlayan sözlük servisi.
    """
    OFFLINE_DICT = {
        "deprecated": {
            "tr": "Kullanımdan kaldırılmış / Eskiye ayrılmış",
            "phonetic": "/ˈdɛprəkeɪtɪd/",
            "pos": "adjective",
            "example": "This API method is deprecated and will be removed."
        },
        "refactor": {
            "tr": "Kodu yeniden yapılandırmak",
            "phonetic": "/riːˈfæktər/",
            "pos": "verb",
            "example": "We need to refactor the code for better performance."
        },
        "override": {
            "tr": "Geçersiz kılmak / Ezmek",
            "phonetic": "/ˌoʊvərˈraɪd/",
            "pos": "verb",
            "example": "Subclasses can override this method."
        },
        "buffer": {
            "tr": "Arabellek / Tampon alan",
            "phonetic": "/ˈbʌfər/",
            "pos": "noun",
            "example": "Data is stored temporarily in the buffer."
        },
        "enjoy": {
            "tr": "Tadını çıkarmak / Keyif almak",
            "phonetic": "/ɪnˈdʒɔɪ/",
            "pos": "verb",
            "example": "Enjoy your stay here!"
        }
    }

    def lookup(self, word: str) -> dict:
        """
        Kelime aramasını gerçekleştirir.
        Döndürür: { "word": str, "tr": str, "phonetic": str, "pos": str, "example": str }
        """
        clean_word = word.strip().lower().strip("().,!?[]\"'")
        if not clean_word:
            return {}

        if clean_word in self.OFFLINE_DICT:
            entry = dict(self.OFFLINE_DICT[clean_word])
            entry["word"] = clean_word
            return entry

        # İnternet araması fallback
        try:
            url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{quote(clean_word)}"
            res = requests.get(url, timeout=1.5)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list) and len(data) > 0:
                    first = data[0]
                    phonetic = first.get("phonetic", "")
                    meanings = first.get("meanings", [])
                    pos = meanings[0].get("partOfSpeech", "") if meanings else ""
                    definitions = meanings[0].get("definitions", []) if meanings else []
                    example = definitions[0].get("example", "") if definitions else ""

                    return {
                        "word": clean_word,
                        "tr": clean_word.capitalize(),
                        "phonetic": phonetic,
                        "pos": pos,
                        "example": example
                    }
        except Exception:
            pass

        return {
            "word": clean_word,
            "tr": clean_word.capitalize(),
            "phonetic": f"/{clean_word}/",
            "pos": "word",
            "example": ""
        }
