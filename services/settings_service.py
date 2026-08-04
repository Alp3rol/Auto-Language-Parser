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
        "hotkey_preset": "Alt+S",
        "enable_live_mode": True,
        "live_interval": 2.0,
        "live_skip_unchanged": True,
        "show_floating_widget": True,
        "floating_opacity": 90,
        "enable_hotkeys": True,
        "selection_hotkey": "<alt>+s",
        "live_hotkey": "<ctrl>+<alt>+l",
        "target_lang": "tr",
        "auto_detect_src": True,
        "enable_selection_translation": True,
        "auto_clipboard_translate": False,
        "selection_translate_hotkey": "Alt+C",
        "enable_in_place": False,
        "enable_context_ai": True,
        "enable_hover_dict": True,
        "hover_delay_ms": 400,
        "enable_vocab_builder": True,
        "ocr_engine": "rapid_paddle",
        "enable_radial_menu": False,
        "enable_hover_lookup": True
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

            # Yeni ayarlar varsa eksikleri tamamla
            updated = False
            for k, v in self.DEFAULT_SETTINGS.items():
                if k not in data:
                    data[k] = v
                    updated = True

            # Kararlılık güncellemeleri: ocr_engine, enable_radial_menu, enable_in_place
            if data.get("ocr_engine") == "auto":
                data["ocr_engine"] = "rapid_paddle"
                updated = True
            if data.get("enable_radial_menu") is True:
                data["enable_radial_menu"] = False
                updated = True
            if data.get("enable_in_place") is True:
                data["enable_in_place"] = False
                updated = True

            if updated:
                self._save_settings(data)
            return data
        except Exception:
            return dict(self.DEFAULT_SETTINGS)
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
