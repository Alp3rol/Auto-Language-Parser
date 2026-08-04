import time
from pynput.keyboard import Key, Controller
from PySide6.QtWidgets import QApplication


class ClipboardService:
    """
    Ekrandaki aktif pencereden seçili metni almak (Ctrl+C simülasyonu) ve pano yönetimi servisi.
    """
    def __init__(self):
        self.keyboard_controller = Controller()

    def capture_selected_text(self) -> str:
        """
        Kullanıcının fare ile seçtiği metni almak için Ctrl+C simüle eder ve panodaki metni döndürür.
        """
        clipboard = QApplication.clipboard()
        initial_text = clipboard.text()

        # Ctrl+C tuş simülasyonu
        try:
            self.keyboard_controller.press(Key.ctrl)
            self.keyboard_controller.press('c')
            self.keyboard_controller.release('c')
            self.keyboard_controller.release(Key.ctrl)
        except Exception as e:
            print(f"[PANO HATASI] Tuş simülasyonu başarısız: {e}")

        # Panonun güncellenmesi için güvenli bekleme (150 ms)
        time.sleep(0.15)

        new_text = clipboard.text()
        if new_text == initial_text:
            time.sleep(0.08)
            new_text = clipboard.text()

        if new_text and new_text.strip():
            return new_text.strip()
        return ""
