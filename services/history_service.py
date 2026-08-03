import os
import json
from datetime import datetime


class HistoryService:
    """
    Çeviri geçmişini saklayan, listeleyen ve yöneten JSON veri servisi.
    """
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        
        os.makedirs(data_dir, exist_ok=True)
        self.filepath = os.path.join(data_dir, "history.json")
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.filepath):
            self._save_data([])

    def _load_data(self) -> list:
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_data(self, data: list):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[GEÇMİŞ HATASI] Veri kaydedilemedi: {e}")

    def add_item(self, original_text: str, translated_text: str, source_lang: str, target_lang: str):
        """Yeni bir çeviri kaydını geçmişe ekler."""
        if not original_text or not translated_text:
            return

        history = self._load_data()
        new_item = {
            "id": len(history) + 1,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "original_text": original_text,
            "translated_text": translated_text,
            "source_lang": source_lang.upper(),
            "target_lang": target_lang.upper()
        }

        # En son yapılan çeviri en başa gelsin (Max 100 kayıt)
        history.insert(0, new_item)
        history = history[:100]
        self._save_data(history)

    def get_history(self) -> list:
        """Tüm çeviri geçmişini döndürür."""
        return self._load_data()

    def clear_history(self):
        """Tüm çeviri geçmişini temizler."""
        self._save_data([])
