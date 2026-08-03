import os
import json


class SettingsService:
    """
    Kullanıcı tercihlerini data/settings.json dosyasında saklayan ve yöneten servis.
    """
    DEFAULT_SETTINGS = {
        "auto_copy": True,
        "auto_tts": False,
        "popup_duration": 0,
        "hotkey_preset": "Alt+S"
    }

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        
        os.makedirs(data_dir, exist_ok=True)
        self.filepath = os.path.join(data_dir, "settings.json")
        self.settings = self._load_settings()

    def _load_settings(self) -> dict:
        if not os.path.exists(self.filepath):
            self._save_settings(self.DEFAULT_SETTINGS)
            return dict(self.DEFAULT_SETTINGS)

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Eksik anahtar varsa varsayılanlar ile doldur
                merged = dict(self.DEFAULT_SETTINGS)
                merged.update(data)
                return merged
        except Exception:
            return dict(self.DEFAULT_SETTINGS)

    def _save_settings(self, settings: dict):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[AYAR HATASI] Ayarlar kaydedilemedi: {e}")

    def get(self, key: str, default=None):
        return self.settings.get(key, default)

    def set(self, key: str, value):
        self.settings[key] = value
        self._save_settings(self.settings)

    def reset_defaults(self):
        self.settings = dict(self.DEFAULT_SETTINGS)
        self._save_settings(self.settings)
        return self.settings
