import os
import sys
from pynput import keyboard as pynput_keyboard

from PySide6.QtCore import QObject, Signal, QRect, Qt, QThread
from PySide6.QtGui import QIcon, QPixmap, QColor, QPainter, QAction, QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QLabel, QSystemTrayIcon, QMenu, QGroupBox, QTextEdit
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ui.selection_overlay import SelectionOverlay
from ui.popup import TranslationPopup, show_error_popup
from services.capture import capture_screen_area
from services.ocr_service import OCRService
from services.translate_service import TranslationService


class TranslationWorkerThread(QThread):
    """
    Ekran kırpma (Qt native grabWindow), OCR (kelime boşluk korumalı) ve Çeviri adımlarını 
    arka plan thread'inde çalıştıran işçi sınıfı.
    """
    finished = Signal(str, str, str, str, QRect, tuple)
    error = Signal(str)

    def __init__(self, rect: QRect, physical_coords: tuple, ocr_service: OCRService, translate_service: TranslationService):
        super().__init__()
        self.rect = rect
        self.physical_coords = physical_coords
        self.ocr_service = ocr_service
        self.translate_service = translate_service

    def run(self):
        try:
            # 1. Qt native grabWindow ile piksel-mükemmel ekran görüntüsü al
            pil_img = capture_screen_area(self.rect)

            # 2. Metni OCR ile çıkar (kelimeler arası boşluk korumalı)
            ocr_text = self.ocr_service.extract_text(pil_img)
            if not ocr_text or not ocr_text.strip():
                self.finished.emit("", "", "auto", "tr", self.rect, self.physical_coords)
                return

            # 3. Metnin dilini otomatik tespit et ve çevir (LibreTranslate)
            translated, src_lang, tgt_lang = self.translate_service.translate(ocr_text)
            self.finished.emit(ocr_text, translated, src_lang, tgt_lang, self.rect, self.physical_coords)

        except ConnectionError as ce:
            self.error.emit(str(ce))
        except Exception as e:
            self.error.emit(f"İşlem sırasında hata oluştu: {e}")


class PynputHotkeyListener(QObject):
    """Windows genelinde (Global) tuş dinleme sağlayan pynput dinleyicisi."""
    triggered = Signal()

    def __init__(self):
        super().__init__()
        self.listener = None

    def start(self):
        def on_activate():
            print("[PYNPUT] Global Kısayol Algılandı!")
            self.triggered.emit()

        hotkeys = {
            '<alt>+s': on_activate,
            '<ctrl>+<alt>+s': on_activate,
            '<f8>': on_activate
        }

        try:
            self.listener = pynput_keyboard.GlobalHotKeys(hotkeys)
            self.listener.start()
            print("[BAŞARILI] Global Kısayol Dinleyicisi Aktif (Alt+S, Ctrl+Alt+S, F8)")
        except Exception as e:
            print(f"[HATA] Global kısayol dinleyicisi başlatılamadı: {e}")

    def stop(self):
        if self.listener:
            self.listener.stop()


def create_app_icon():
    """Programatik olarak şık bir uygulama simgesi çizer."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    painter.setBrush(QColor(0, 120, 212))
    painter.setPen(QColor(0, 90, 160))
    painter.drawEllipse(2, 2, 60, 60)

    painter.setPen(QColor(255, 255, 255))
    font = painter.font()
    font.setPointSize(26)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "T")
    painter.end()

    return QIcon(pixmap)


class MainWindow(QMainWindow):
    """Kırpma Kayması ve Kelime Birleşme Düzeltmeli Ana Pencere"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Windows Ekran Çevirici (Screen Translator)")
        self.resize(540, 480)
        self.setWindowIcon(create_app_icon())

        self.ocr_service = OCRService()
        self.translate_service = TranslationService()
        self.worker_thread = None
        self.active_popup = None

        self.overlay = SelectionOverlay()
        self.overlay.area_selected.connect(self.on_area_selected)
        self.overlay.cancelled.connect(self.on_selection_cancelled)

        self.setup_ui()
        self.setup_shortcuts()
        self.setup_tray()
        self.setup_pynput_hotkey()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #181818;
            }
            QLabel {
                color: #FFFFFF;
                font-family: 'Segoe UI', sans-serif;
            }
            QPushButton {
                background-color: #0078D4;
                color: white;
                font-size: 15px;
                font-weight: bold;
                border-radius: 8px;
                padding: 12px;
                border: none;
            }
            QPushButton:hover {
                background-color: #106EBE;
            }
            QPushButton:pressed {
                background-color: #005A9E;
            }
            QGroupBox {
                border: 1px solid #333333;
                border-radius: 8px;
                margin-top: 10px;
                color: #0078D4;
                font-weight: bold;
            }
            QTextEdit {
                background-color: #252526;
                color: #00FF88;
                border: 1px solid #3C3C3C;
                border-radius: 6px;
                padding: 8px;
                font-family: 'Consolas', 'Segoe UI', monospace;
                font-size: 13px;
            }
        """)

        title_label = QLabel("Ekran Çeviri Kontrol Paneli")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        self.select_btn = QPushButton("🎯 Ekran Seçimi Yap (Alt+S veya F8)")
        self.select_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.select_btn.clicked.connect(self.start_selection_safe)
        layout.addWidget(self.select_btn)

        info_group = QGroupBox("Son Çeviri & OCR Sonucu")
        group_layout = QVBoxLayout(info_group)

        self.status_label = QLabel("Kısayola basıp ekran üzerinde çevrilecek alanı seçin.")
        self.status_label.setStyleSheet("color: #AAAAAA; font-size: 12px;")
        group_layout.addWidget(self.status_label)

        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setPlaceholderText("OCR ve Çeviri sonuçları burada görünecektir...")
        group_layout.addWidget(self.text_display)

        layout.addWidget(info_group)

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Alt+S"), self, self.start_selection_safe)
        QShortcut(QKeySequence("F8"), self, self.start_selection_safe)
        QShortcut(QKeySequence("Ctrl+Alt+S"), self, self.start_selection_safe)

    def setup_pynput_hotkey(self):
        self.hotkey_listener = PynputHotkeyListener()
        self.hotkey_listener.triggered.connect(self.start_selection_safe)
        self.hotkey_listener.start()

    def start_selection_safe(self):
        self.overlay.start_selection()

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(create_app_icon(), self)
        self.tray_icon.setToolTip("Ekran Çevirici (Alt+S / F8)")

        menu = QMenu()
        show_action = QAction("Pencereyi Göster", self)
        show_action.triggered.connect(self.show_and_activate)
        menu.addAction(show_action)

        select_action = QAction("Seçim Yap (Alt+S / F8)", self)
        select_action.triggered.connect(self.start_selection_safe)
        menu.addAction(select_action)

        menu.addSeparator()
        quit_action = QAction("Çıkış", self)
        quit_action.triggered.connect(self.close_app)
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.show_and_activate()

    def show_and_activate(self):
        self.showNormal()
        self.activateWindow()

    def on_area_selected(self, rect: QRect, physical_coords: tuple):
        self.status_label.setText("⏳ Metin okunuyor ve çevriliyor...")
        self.status_label.setStyleSheet("color: #00E5FF; font-weight: bold; font-size: 12px;")

        self.worker_thread = TranslationWorkerThread(rect, physical_coords, self.ocr_service, self.translate_service)
        self.worker_thread.finished.connect(self.on_translation_finished)
        self.worker_thread.error.connect(self.on_translation_error)
        self.worker_thread.start()

    def on_translation_finished(self, ocr_text: str, translated: str, src_lang: str, tgt_lang: str, rect: QRect, physical_coords: tuple):
        if not ocr_text.strip():
            self.status_label.setText("⚠️ Okunabilir metin bulunamadı.")
            self.status_label.setStyleSheet("color: #FFCC00; font-weight: bold; font-size: 12px;")
            self.text_display.setText("(Seçilen alanda okunabilir metin bulunamadı)")

            show_error_popup(
                self,
                "Metin Okunamadı",
                "Seçtiğiniz alanda okunabilir herhangi bir Türkçe veya İngilizce metin tespit edilemedi."
            )
            return

        self.status_label.setText(f"✅ Çeviri Başarılı ({src_lang.upper()} ➔ {tgt_lang.upper()})")
        self.status_label.setStyleSheet("color: #00FF88; font-weight: bold; font-size: 12px;")

        display_content = f"【Orijinal Metin ({src_lang.upper()})】:\n{ocr_text}\n\n【Çeviri ({tgt_lang.upper()})】:\n{translated}"
        self.text_display.setText(display_content)

        print("\n" + "=" * 60)
        print(f" [ÇEVİRİ SONUCU] ({src_lang.upper()} -> {tgt_lang.upper()})")
        print(" -> Orijinal Metin:")
        print(f"    {ocr_text}")
        print(" -> Çeviri:")
        print(f"    {translated}")
        print("=" * 60 + "\n")
        sys.stdout.flush()

        if self.active_popup is not None:
            try:
                self.active_popup.close()
                self.active_popup.deleteLater()
            except Exception:
                pass
            self.active_popup = None

        self.active_popup = TranslationPopup(ocr_text, translated, src_lang, tgt_lang, rect)
        self.active_popup.show()

    def on_translation_error(self, error_msg: str):
        self.status_label.setText(f"❌ Hata: {error_msg}")
        self.status_label.setStyleSheet("color: #FF6B6B; font-size: 12px;")
        print(f"[HATA] {error_msg}")
        sys.stdout.flush()

        show_error_popup(
            self,
            "Bağlantı / Çeviri Hatası",
            error_msg
        )

    def on_selection_cancelled(self):
        self.status_label.setText("Seçim iptal edildi (ESC tuşlandı veya alan çok küçük).")
        self.status_label.setStyleSheet("color: #FF6B6B; font-size: 12px;")
        sys.stdout.flush()

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def close_app(self):
        if hasattr(self, 'hotkey_listener'):
            self.hotkey_listener.stop()
        QApplication.quit()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
