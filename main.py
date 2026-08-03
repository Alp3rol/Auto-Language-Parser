import os
import sys
from pynput import keyboard as pynput_keyboard

from PySide6.QtCore import QObject, Signal, QRect, Qt, QThread, QEvent
from PySide6.QtGui import QIcon, QPixmap, QColor, QPainter, QAction, QFont, QKeySequence, QShortcut, QGuiApplication
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSystemTrayIcon, QMenu, QGroupBox, QTextEdit,
    QTabWidget
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ui.selection_overlay import SelectionOverlay
from ui.popup import TranslationPopup, LoadingPopup, show_error_popup
from ui.history_tab import HistoryTab
from ui.settings_tab import SettingsTab
from services.capture import capture_screen_area
from services.ocr_service import OCRService
from services.translate_service import TranslationService
from services.tts_service import TTSService
from services.history_service import HistoryService
from services.settings_service import SettingsService


class TranslationWorkerThread(QThread):
    """Ekran kırpma, OCR ve Çeviri adımlarını arka plan thread'inde çalıştıran işçi sınıfı."""
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
            pil_img = capture_screen_area(self.rect)
            ocr_text = self.ocr_service.extract_text(pil_img)

            if not ocr_text or not ocr_text.strip():
                self.finished.emit("", "", "auto", "tr", self.rect, self.physical_coords)
                return

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
    """A.L.P. (Auto Language Parser) Ana Uygulama Penceresi"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("A.L.P. (Auto Language Parser)")
        self.resize(540, 480)
        self.setWindowIcon(create_app_icon())

        # Görev çubuğunda görünmemesi için Tool bayrağı ekle
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.Tool)

        # Servisleri başlat
        self.ocr_service = OCRService()
        self.translate_service = TranslationService()
        self.tts_service = TTSService()
        self.history_service = HistoryService()
        self.settings_service = SettingsService()

        self.worker_thread = None
        self.active_popup = None

        # Seçim Overlay bileşeni
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
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # Tab Widget (Sekmeli Görünüm)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #333333;
                background-color: #181818;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #252526;
                color: #AAAAAA;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #0078D4;
                color: #FFFFFF;
            }
            QTabBar::tab:hover:!selected {
                background-color: #2D2D30;
                color: #FFFFFF;
            }
        """)

        # Sekme 1: Çeviri Kontrol Paneli
        translation_panel = QWidget()
        t_layout = QVBoxLayout(translation_panel)
        t_layout.setSpacing(10)
        t_layout.setContentsMargins(12, 12, 12, 12)

        title_label = QLabel("A.L.P. Ekran Çeviri Kontrol Paneli")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t_layout.addWidget(title_label)

        self.select_btn = QPushButton("🎯 Ekran Seçimi Yap (Alt+S veya F8)")
        self.select_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.select_btn.clicked.connect(self.start_selection_safe)
        t_layout.addWidget(self.select_btn)

        info_group = QGroupBox("Son Çeviri & OCR Sonucu")
        group_layout = QVBoxLayout(info_group)

        self.status_label = QLabel("Kısayola basıp ekran üzerinde çevrilecek alanı seçin.")
        self.status_label.setStyleSheet("color: #AAAAAA; font-size: 11px;")
        group_layout.addWidget(self.status_label)

        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setPlaceholderText("OCR ve Çeviri sonuçları burada görünecektir...")
        group_layout.addWidget(self.text_display)

        action_layout = QHBoxLayout()
        self.listen_btn = QPushButton("🔊 Son Çeviriyi Dinle")
        self.listen_btn.setStyleSheet("background-color: #2D2D30; color: #00E5FF;")
        self.listen_btn.clicked.connect(self.speak_current_translation)
        action_layout.addWidget(self.listen_btn)

        self.copy_btn = QPushButton("📋 Çeviriyi Kopyala")
        self.copy_btn.setStyleSheet("background-color: #2D2D30; color: #00FF88;")
        self.copy_btn.clicked.connect(self.copy_current_translation)
        action_layout.addWidget(self.copy_btn)

        group_layout.addLayout(action_layout)
        t_layout.addWidget(info_group)

        # Sekme 2: Çeviri Geçmişi Tabı
        self.history_tab = HistoryTab(self.history_service, self.tts_service)

        # Sekme 3: Ayarlar Tabı
        self.settings_tab = SettingsTab(self.settings_service)

        # Sekmeleri Ekle
        self.tabs.addTab(translation_panel, "🎯 Çeviri Paneli")
        self.tabs.addTab(self.history_tab, "📚 Çeviri Geçmişi")
        self.tabs.addTab(self.settings_tab, "⚙️ Ayarlar")

        main_layout.addWidget(self.tabs)

        self.last_translated_text = ""
        self.last_target_lang = "tr"

    def position_at_bottom_right(self):
        """Pencereyi ekranın sağ alt köşesine (görev çubuğunun hemen üstüne) hizalar."""
        screen = QGuiApplication.primaryScreen()
        avail_geo = screen.availableGeometry()

        win_w = self.width()
        win_h = self.height()

        x = avail_geo.right() - win_w - 12
        y = avail_geo.bottom() - win_h - 12

        self.setGeometry(x, y, win_w, win_h)

    def changeEvent(self, event):
        """Pencere odağını kaybettiğinde (dışarı tıklandığında) otomatik tepsye gizlenir."""
        if event.type() == QEvent.Type.ActivationChange:
            if not self.isActiveWindow():
                if not QApplication.activeModalWidget():
                    self.hide()
        super().changeEvent(event)

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
        self.tray_icon.setToolTip("A.L.P. (Auto Language Parser)")

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
        self.position_at_bottom_right()
        self.showNormal()
        self.activateWindow()

    def speak_current_translation(self):
        if self.last_translated_text:
            self.tts_service.speak(self.last_translated_text, self.last_target_lang)

    def copy_current_translation(self):
        if self.last_translated_text:
            QApplication.clipboard().setText(self.last_translated_text)
            self.status_label.setText("📋 Çeviri panoya kopyalandı!")
            self.status_label.setStyleSheet("color: #00FF88; font-weight: bold;")

    def on_area_selected(self, rect: QRect, physical_coords: tuple):
        self.status_label.setText("⏳ Metin okunuyor ve çevriliyor...")
        self.status_label.setStyleSheet("color: #00E5FF; font-weight: bold; font-size: 12px;")

        # Eski popup varsa kapat ve anlık yükleme göstergesini göster
        if self.active_popup is not None:
            try:
                self.active_popup.close()
                self.active_popup.deleteLater()
            except Exception:
                pass
            self.active_popup = None

        self.active_popup = LoadingPopup(rect)
        self.active_popup.show()

        self.worker_thread = TranslationWorkerThread(rect, physical_coords, self.ocr_service, self.translate_service)
        self.worker_thread.finished.connect(self.on_translation_finished)
        self.worker_thread.error.connect(self.on_translation_error)
        self.worker_thread.start()

    def on_translation_finished(self, ocr_text: str, translated: str, src_lang: str, tgt_lang: str, rect: QRect, physical_coords: tuple):
        # Yükleme popup'ını kapat
        if self.active_popup is not None:
            try:
                self.active_popup.close()
                self.active_popup.deleteLater()
            except Exception:
                pass
            self.active_popup = None

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

        self.last_translated_text = translated
        self.last_target_lang = tgt_lang

        # Geçmişe kaydet ve Geçmiş Tablosunu Yenile
        self.history_service.add_item(ocr_text, translated, src_lang, tgt_lang)
        self.history_tab.load_history()

        # Otomatik Kopyalama
        if self.settings_service.get("auto_copy", True):
            QApplication.clipboard().setText(translated)

        # Otomatik Sesli Okuma
        if self.settings_service.get("auto_tts", False):
            self.tts_service.speak(translated, tgt_lang)

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

        duration = self.settings_service.get("popup_duration", 0)
        self.active_popup = TranslationPopup(ocr_text, translated, src_lang, tgt_lang, rect, duration_sec=duration)
        self.active_popup.copy_requested.connect(lambda text: QApplication.clipboard().setText(text))
        self.active_popup.speak_requested.connect(lambda text, lang: self.tts_service.speak(text, lang))
        self.active_popup.show()

    def on_translation_error(self, error_msg: str):
        if self.active_popup is not None:
            try:
                self.active_popup.close()
                self.active_popup.deleteLater()
            except Exception:
                pass
            self.active_popup = None

        self.status_label.setText(f"❌ Hata: {error_msg}")
        self.status_label.setStyleSheet("color: #FF6B6B; font-size: 12px;")
        print(f"[HATA] {error_msg}")
        sys.stdout.flush()

        show_error_popup(self, "Bağlantı / Çeviri Hatası", error_msg)

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
    window.hide()

    window.tray_icon.showMessage(
        "A.L.P. (Auto Language Parser)",
        "Uygulama arka planda ve sistem tepsisinde aktif.\nKısayollar: Alt+S veya F8",
        QSystemTrayIcon.MessageIcon.Information,
        3000
    )

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
