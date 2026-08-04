import os
import sys
import time

from PySide6.QtCore import QObject, Signal, QRect, Qt, QThread, QEvent, QTimer, QPoint
from PySide6.QtGui import QIcon, QPixmap, QColor, QPainter, QAction, QFont, QKeySequence, QShortcut, QGuiApplication, QCursor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSystemTrayIcon, QMenu, QTextEdit,
    QTabWidget
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ui.selection_overlay import SelectionOverlay
from ui.popup import TranslationPopup, LoadingPopup, show_error_popup
from ui.live_subtitle_overlay import LiveSubtitleOverlay
from ui.floating_widget import FloatingWidget
from ui.history_tab import HistoryTab
from ui.settings_tab import SettingsTab
from ui.vocab_tab import VocabTab
from ui.hover_tooltip import HoverTooltip
from ui.in_place_overlay import InPlaceOverlay
from ui.radial_menu import RadialMenu
from ui.tray_manager import TrayManager, create_app_icon
from services.capture import capture_screen_area
from services.ocr_service import OCRService
from services.translate_service import TranslationService
from services.tts_service import TTSService
from services.history_service import HistoryService
from services.settings_service import SettingsService
from services.clipboard_service import ClipboardService
from services.context_engine import ContextEngine
from services.dictionary_service import DictionaryService
from services.vocab_service import VocabService
from services.privacy_service import PrivacyService
from services.hotkey_manager import HotkeyManager



def safe_set_clipboard(text: str):
    """Panoya metin yazarken sinyalleri geçici olarak engelleyerek sonsuz kilitlenme döngüsünü önler."""
    try:
        cb = QApplication.clipboard()
        cb.blockSignals(True)
        cb.setText(text)
        cb.blockSignals(False)
    except Exception:
        pass


class TranslationWorkerThread(QThread):
    """Ekran kırpma, OCR ve Çeviri adımlarını arka plan thread'inde çalıştıran işçi sınıfı."""
    finished = Signal(str, str, str, str, QRect, tuple)
    error = Signal(str)

    def __init__(self, rect: QRect, physical_coords: tuple, ocr_service: OCRService,
                 translate_service: TranslationService, target_lang: str = "tr", auto_detect: bool = True, ocr_engine: str = "auto"):
        super().__init__()
        self.rect = rect
        self.physical_coords = physical_coords
        self.ocr_service = ocr_service
        self.translate_service = translate_service
        self.target_lang = target_lang
        self.auto_detect = auto_detect
        self.ocr_engine = ocr_engine

    def run(self):
        try:
            pil_img = capture_screen_area(self.rect)
            ocr_text = self.ocr_service.extract_text(pil_img, engine=self.ocr_engine)

            if not ocr_text or not ocr_text.strip():
                self.finished.emit("", "", "auto", self.target_lang, self.rect, self.physical_coords)
                return

            translated, src_lang, tgt_lang = self.translate_service.translate(
                ocr_text, target_lang=self.target_lang, auto_detect=self.auto_detect
            )
            self.finished.emit(ocr_text, translated, src_lang, tgt_lang, self.rect, self.physical_coords)

        except ConnectionError as ce:
            self.error.emit(str(ce))
        except Exception as e:
            self.error.emit(f"İşlem sırasında hata oluştu: {e}")


class TextTranslationWorkerThread(QThread):
    """Doğrudan seçili metni alan ve çeviri sonucunu imleç konumuna döndüren işçi sınıfı."""
    finished = Signal(str, str, str, str, QPoint)
    error = Signal(str)

    def __init__(self, text: str, cursor_pos: QPoint, translate_service: TranslationService,
                 target_lang: str = "tr", auto_detect: bool = True):
        super().__init__()
        self.text = text
        self.cursor_pos = cursor_pos
        self.translate_service = translate_service
        self.target_lang = target_lang
        self.auto_detect = auto_detect

    def run(self):
        try:
            translated, src_lang, tgt_lang = self.translate_service.translate(
                self.text, target_lang=self.target_lang, auto_detect=self.auto_detect
            )
            self.finished.emit(self.text, translated, src_lang, tgt_lang, self.cursor_pos)
        except Exception as e:
            self.error.emit(f"Metin çevirisi hatası: {e}")


class LiveTranslationWorkerThread(QThread):
    """Canlı altyazı modunda ekranı düzenli aralıklarla tarayan işçi sınıfı."""
    translation_updated = Signal(str, str, str, str)
    error = Signal(str)

    def __init__(self, rect: QRect, ocr_service: OCRService, translate_service: TranslationService,
                 interval: float = 2.0, skip_unchanged: bool = True, target_lang: str = "tr", auto_detect: bool = True, ocr_engine: str = "auto"):
        super().__init__()
        self.rect = rect
        self.ocr_service = ocr_service
        self.translate_service = translate_service
        self.interval = max(0.5, interval)
        self.skip_unchanged = skip_unchanged
        self.target_lang = target_lang
        self.auto_detect = auto_detect
        self.ocr_engine = ocr_engine

        self.is_running = True
        self.is_paused = False
        self.last_ocr_text = ""
        self.last_img_hash = None

    def stop(self):
        self.is_running = False

    def set_paused(self, paused: bool):
        self.is_paused = paused

    def _compute_img_hash(self, pil_img):
        if pil_img is None:
            return None
        # 16x16 thumbnail for fast image hash comparison before OCR
        thumb = pil_img.resize((16, 16)).convert("L")
        return thumb.tobytes()

    def run(self):
        while self.is_running:
            if not self.is_paused:
                try:
                    pil_img = capture_screen_area(self.rect)

                    # Görsel değişmediyse OCR çağrısını tamamen atla (95% CPU tasarrufu)
                    if self.skip_unchanged:
                        img_hash = self._compute_img_hash(pil_img)
                        if img_hash and img_hash == self.last_img_hash:
                            time.sleep(self.interval)
                            continue
                        self.last_img_hash = img_hash

                    ocr_text = self.ocr_service.extract_text(pil_img, engine=self.ocr_engine)

                    if ocr_text and ocr_text.strip():
                        if not (self.skip_unchanged and ocr_text.strip() == self.last_ocr_text.strip()):
                            self.last_ocr_text = ocr_text
                            translated, src_lang, tgt_lang = self.translate_service.translate(
                                ocr_text, target_lang=self.target_lang, auto_detect=self.auto_detect
                            )
                            self.translation_updated.emit(ocr_text, translated, src_lang, tgt_lang)
                except Exception as e:
                    print(f"[CANLI MOD UYARISI] {e}")

            time.sleep(self.interval)







class MainWindow(QMainWindow):
    """A.L.P. (Auto Language Parser) Ana Uygulama Penceresi"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("A.L.P. (Auto Language Parser)")
        self.resize(540, 480)
        self.setWindowIcon(create_app_icon())

        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.Tool)

        # Servisleri başlat
        self.privacy_service = PrivacyService()
        self.ocr_service = OCRService()
        self.translate_service = TranslationService(privacy_service=self.privacy_service)
        self.tts_service = TTSService()
        self.history_service = HistoryService()
        self.settings_service = SettingsService()
        self.clipboard_service = ClipboardService()
        self.context_engine = ContextEngine()
        self.dictionary_service = DictionaryService()
        self.vocab_service = VocabService()
        self.hover_tooltip = HoverTooltip()
        self.in_place_overlay = None


        self.worker_thread = None
        self.text_worker = None
        self.live_thread = None
        self.active_popup = None
        self.live_overlay = None
        self.floating_widget = None
        self.is_selecting_for_live = False
        self._last_auto_clip = ""

        self.last_translated_text = ""
        self.last_target_lang = "tr"

        # Seçim Overlay bileşeni
        self.overlay = SelectionOverlay()
        self.overlay.area_selected.connect(self.on_area_selected)
        self.overlay.cancelled.connect(self.on_selection_cancelled)

        self.setup_ui()
        self.setup_shortcuts()
        self.setup_tray()
        self.setup_pynput_hotkey()
        self.setup_floating_widget()
        self.update_shortcut_labels()

        # Otomatik Pano Takibi Dinleyicisi
        QApplication.clipboard().dataChanged.connect(self.on_clipboard_data_changed)

        # Ayarlar kaydedildiğinde servisleri yeniden yükle
        self.settings_tab.settings_saved.connect(self.on_settings_saved)

    def setup_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        central_widget.setStyleSheet("""
            QWidget#centralWidget {
                background-color: #09090B;
                border: 1px solid #27272A;
                border-radius: 10px;
            }
            QWidget {
                color: #F4F4F5;
                font-family: 'Segoe UI', -apple-system, sans-serif;
            }
            QTabWidget::pane {
                border: 1px solid #27272A;
                background-color: #18181B;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: transparent;
                color: #A1A1AA;
                padding: 7px 16px;
                font-weight: 600;
                font-size: 12px;
                border-radius: 6px;
                margin: 2px;
            }
            QTabBar::tab:selected {
                background-color: #27272A;
                color: #F4F4F5;
            }
            QTabBar::tab:hover:!selected {
                background-color: #18181B;
                color: #FFFFFF;
            }
            QTextEdit {
                background-color: #09090B;
                color: #F4F4F5;
                border: 1px solid #27272A;
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
                line-height: 1.4;
            }
        """)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)

        # 1. Özel Frameless Başlık Çubuğu (TitleBar)
        title_bar = QWidget()
        title_bar.setFixedHeight(38)
        title_bar.setStyleSheet("background-color: #18181B; border-top-left-radius: 9px; border-top-right-radius: 9px; border-bottom: 1px solid #27272A;")
        tb_layout = QHBoxLayout(title_bar)
        tb_layout.setContentsMargins(12, 0, 8, 0)

        app_title = QLabel("⚡ A.L.P. Screen Translator")
        app_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #F4F4F5;")
        tb_layout.addWidget(app_title)

        tb_layout.addStretch()

        btn_min = QPushButton("—")
        btn_min.setFixedSize(28, 24)
        btn_min.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_min.setStyleSheet("QPushButton { background: transparent; color: #A1A1AA; border: none; font-size: 12px; } QPushButton:hover { background-color: #27272A; color: #FFF; border-radius: 4px; }")
        btn_min.clicked.connect(self.hide)
        tb_layout.addWidget(btn_min)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(28, 24)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("QPushButton { background: transparent; color: #A1A1AA; border: none; font-size: 12px; } QPushButton:hover { background-color: #EF4444; color: #FFF; border-radius: 4px; }")
        btn_close.clicked.connect(self.hide)
        tb_layout.addWidget(btn_close)

        main_layout.addWidget(title_bar)

        # İç İçerik Alanı
        content_widget = QWidget()
        c_layout = QVBoxLayout(content_widget)
        c_layout.setContentsMargins(10, 10, 10, 10)
        c_layout.setSpacing(10)

        self.tabs = QTabWidget()

        # Sekme 1: Çeviri Kontrol Paneli
        translation_panel = QWidget()
        t_layout = QVBoxLayout(translation_panel)
        t_layout.setSpacing(10)
        t_layout.setContentsMargins(10, 10, 10, 10)

        # Butonlar Yan Yana
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.select_btn = QPushButton("🎯 Ekran Seçimi Yap")
        self.select_btn.setFixedHeight(40)
        self.select_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.select_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078D4;
                color: #FFFFFF;
                font-size: 13px;
                font-weight: 700;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #106EBE;
            }
        """)
        self.select_btn.clicked.connect(self.start_selection_safe)
        btn_layout.addWidget(self.select_btn, stretch=2)

        self.btn_translate_selection = QPushButton("📋 Seçili Metni Çevir")
        self.btn_translate_selection.setFixedHeight(40)
        self.btn_translate_selection.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_translate_selection.setStyleSheet("""
            QPushButton {
                background-color: #18181B;
                color: #00FF88;
                font-size: 12px;
                font-weight: 700;
                border-radius: 6px;
                border: 1px solid #00FF88;
            }
            QPushButton:hover {
                background-color: #00FF88;
                color: #000000;
            }
        """)
        self.btn_translate_selection.clicked.connect(self.translate_selected_text_at_cursor)
        btn_layout.addWidget(self.btn_translate_selection, stretch=2)

        self.live_btn = QPushButton("📺 Canlı Mod")
        self.live_btn.setFixedHeight(40)
        self.live_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.live_btn.setStyleSheet("""
            QPushButton {
                background-color: #18181B;
                color: #00E5FF;
                font-size: 12px;
                font-weight: 700;
                border-radius: 6px;
                border: 1px solid #00E5FF;
            }
            QPushButton:hover {
                background-color: #00E5FF;
                color: #000000;
            }
        """)
        self.live_btn.clicked.connect(self.start_live_selection)
        btn_layout.addWidget(self.live_btn, stretch=1)

        t_layout.addLayout(btn_layout)

        # Son Çeviri Kartı
        result_card = QWidget()
        result_card.setStyleSheet("background-color: #18181B; border: 1px solid #27272A; border-radius: 8px;")
        rc_layout = QVBoxLayout(result_card)
        rc_layout.setContentsMargins(12, 12, 12, 12)
        rc_layout.setSpacing(8)

        lbl_hdr = QLabel("SON ÇEVİRİ VE OCR SONUCU")
        lbl_hdr.setStyleSheet("font-size: 11px; font-weight: 700; color: #A1A1AA; letter-spacing: 0.5px; border: none; background: transparent;")
        rc_layout.addWidget(lbl_hdr)

        self.status_label = QLabel("Kısayola basıp (Alt+S) ekran alanı veya metin seçip (Alt+C) çevirin.")
        self.status_label.setStyleSheet("color: #71717A; font-size: 12px; border: none; background: transparent;")
        rc_layout.addWidget(self.status_label)

        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setPlaceholderText("OCR ve Çeviri sonuçları burada görünecektir...")
        rc_layout.addWidget(self.text_display)

        action_layout = QHBoxLayout()
        self.listen_btn = QPushButton("🔊 Son Çeviriyi Dinle")
        self.listen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.listen_btn.setStyleSheet("""
            QPushButton {
                background-color: #27272A;
                color: #F4F4F5;
                border: 1px solid #3F3F46;
                border-radius: 6px;
                padding: 8px 12px;
                font-weight: 600;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #3F3F46;
            }
        """)
        self.listen_btn.clicked.connect(self.speak_current_translation)
        action_layout.addWidget(self.listen_btn)

        self.copy_btn = QPushButton("📋 Çeviriyi Kopyala")
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #27272A;
                color: #F4F4F5;
                border: 1px solid #3F3F46;
                border-radius: 6px;
                padding: 8px 12px;
                font-weight: 600;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #3F3F46;
            }
        """)
        self.copy_btn.clicked.connect(self.copy_current_translation)
        action_layout.addWidget(self.copy_btn)

        rc_layout.addLayout(action_layout)
        t_layout.addWidget(result_card)

        # Sekme 2: Kelime Öğrenme & Anki Kartları Tabı
        self.vocab_tab = VocabTab(self.vocab_service)

        # Sekme 3: Çeviri Geçmişi Tabı
        self.history_tab = HistoryTab(self.history_service, self.tts_service)

        # Sekme 4: Ayarlar Tabı
        self.settings_tab = SettingsTab(self.settings_service)

        # Sekmeleri Ekle
        self.tabs.addTab(translation_panel, "🎯 Çeviri Paneli")
        self.tabs.addTab(self.vocab_tab, "🎓 Kelime Kartları")
        self.tabs.addTab(self.history_tab, "📚 Geçmiş")
        self.tabs.addTab(self.settings_tab, "⚙️ Ayarlar")

        c_layout.addWidget(self.tabs)
        main_layout.addWidget(content_widget)

    def setup_floating_widget(self):
        show_floating = self.settings_service.get("show_floating_widget", True)
        opacity = self.settings_service.get("floating_opacity", 90)

        if self.floating_widget is None:
            self.floating_widget = FloatingWidget(opacity=opacity)
            self.floating_widget.capture_requested.connect(self.start_selection_safe)
            self.floating_widget.selection_requested.connect(self.translate_selected_text_at_cursor)
            self.floating_widget.live_requested.connect(self.start_live_selection)
            self.floating_widget.settings_requested.connect(self.show_and_activate)

            screen = QGuiApplication.primaryScreen()
            avail_geo = screen.availableGeometry()
            self.floating_widget.move(avail_geo.right() - 290, avail_geo.top() + 100)

        if show_floating:
            self.floating_widget.set_opacity_percent(opacity)
            self.floating_widget.show()
        else:
            self.floating_widget.hide()

    def update_shortcut_labels(self):
        """Aktif kısayol ayarlarını arayüzdeki tüm durumlara ve araç çubuklarına dinamik yansıtır."""
        crop_preset = self.settings_service.get("hotkey_preset", "Alt+S")
        sel_preset = self.settings_service.get("selection_translate_hotkey", "Alt+C")

        if hasattr(self, 'status_label') and self.status_label:
            self.status_label.setText(f"Kısayola basıp ({crop_preset}) ekran alanı veya metin seçip ({sel_preset}) çevirin.")

        if hasattr(self, 'floating_widget') and self.floating_widget:
            self.floating_widget.update_tooltips(crop_preset, sel_preset)

        if hasattr(self, 'tray_manager') and self.tray_manager:
            self.tray_manager.update_menu_labels(crop_preset, sel_preset)

    def on_settings_saved(self):
        self.setup_shortcuts()
        self.setup_pynput_hotkey()
        self.setup_floating_widget()
        self.update_shortcut_labels()

    def _cleanup_thread(self, thread_attr: str):
        thread = getattr(self, thread_attr, None)
        if thread is not None:
            try:
                if thread.isRunning():
                    thread.requestInterruption()
                    thread.quit()
                    if not thread.wait(800):
                        thread.terminate()
            except Exception:
                pass
            setattr(self, thread_attr, None)

    def translate_selected_text_at_cursor(self):
        enable_sel = self.settings_service.get("enable_selection_translation", True)
        if not enable_sel:
            show_error_popup(self, "Seçili Metin Çevirisi Kapalı", "Bu özellik Ayarlar sekmesinden kapatılmıştır.")
            return

        selected_text = self.clipboard_service.capture_selected_text()
        if not selected_text or not selected_text.strip():
            self.status_label.setText("⚠️ Seçili metin bulunamadı. Lütfen önce metni fare ile seçin.")
            self.status_label.setStyleSheet("color: #FFCC00; font-weight: bold;")
            return

        cursor_pos = QCursor.pos()
        target_lang = self.settings_service.get("target_lang", "tr")
        auto_detect = self.settings_service.get("auto_detect_src", True)

        self._cleanup_thread('text_worker')
        self.text_worker = TextTranslationWorkerThread(
            selected_text, cursor_pos, self.translate_service,
            target_lang=target_lang, auto_detect=auto_detect
        )
        self.text_worker.finished.connect(self.on_selected_text_translation_finished)
        self.text_worker.error.connect(self.on_translation_error)
        self.text_worker.start()

    def on_selected_text_translation_finished(self, original_text: str, translated: str, src_lang: str, tgt_lang: str, cursor_pos: QPoint):
        if self.settings_service.get("enable_context_ai", True):
            translated = self.context_engine.adapt_translation(original_text, translated)

        if self.settings_service.get("enable_vocab_builder", True):
            self.vocab_service.add_word(original_text, translated, src_lang, tgt_lang)
            self.vocab_tab.load_due_cards()
            self.vocab_tab.load_vocab_table()

        self.last_translated_text = translated
        self.last_target_lang = tgt_lang
        self._last_auto_clip = translated.strip()
        self.history_service.add_item(original_text, translated, src_lang, tgt_lang)
        self.history_tab.load_history()

        if self.settings_service.get("auto_copy", True):
            safe_set_clipboard(translated)

        if self.settings_service.get("auto_tts", False):
            self.tts_service.speak(translated, tgt_lang)

        self.status_label.setText(f"✅ Seçili Metin Çevirisi Başarılı ({src_lang.upper()} ➔ {tgt_lang.upper()})")
        self.status_label.setStyleSheet("color: #00FF88; font-weight: bold; font-size: 12px;")

        display_content = f"【Seçili Metin ({src_lang.upper()})】:\n{original_text}\n\n【Çeviri ({tgt_lang.upper()})】:\n{translated}"
        self.text_display.setText(display_content)

        rect = QRect(cursor_pos.x(), cursor_pos.y(), 180, 40)
        duration = self.settings_service.get("popup_duration", 0)

        self._clear_active_popup()
        self.active_popup = TranslationPopup(original_text, translated, src_lang, tgt_lang, rect, duration_sec=duration, is_text_selection=True)
        self.active_popup.copy_requested.connect(lambda text: safe_set_clipboard(text))
        self.active_popup.speak_requested.connect(lambda text, lang: self.tts_service.speak(text, lang))
        self.active_popup.ai_action_requested.connect(self.on_ai_action_requested)
        self.active_popup.show()

    def on_ai_action_requested(self, action_type: str, target_text: str):
        result_text = self.context_engine.process_ai_action(action_type, target_text, translate_service=self.translate_service)
        
        rect = QRect(QCursor.pos().x(), QCursor.pos().y(), 360, 120)
        if self.active_popup and self.active_popup.isVisible():
            rect = self.active_popup.geometry()

        self._clear_active_popup()
        self.active_popup = TranslationPopup(target_text, result_text, "ai", "tr", rect, duration_sec=0)
        if not self.active_popup.is_pinned:
            self.active_popup.toggle_pin()
        self.active_popup.copy_requested.connect(lambda text: safe_set_clipboard(text))
        self.active_popup.speak_requested.connect(lambda text, lang: self.tts_service.speak(text, lang))
        self.active_popup.ai_action_requested.connect(self.on_ai_action_requested)
        self.active_popup.show()

    def on_clipboard_data_changed(self):
        if not self.settings_service.get("auto_clipboard_translate", False):
            return

        now = time.time()
        if now - getattr(self, '_last_clip_time', 0) < 1.5:
            return
        self._last_clip_time = now

        if getattr(self, '_is_processing_clipboard', False):
            return
        self._is_processing_clipboard = True

        try:
            text = QApplication.clipboard().text()
            if not text or not text.strip():
                return

            clean_text = text.strip()
            if clean_text == getattr(self, '_last_auto_clip', '').strip() or clean_text == getattr(self, 'last_translated_text', '').strip():
                return

            self._last_auto_clip = clean_text
            cursor_pos = QCursor.pos()
            target_lang = self.settings_service.get("target_lang", "tr")
            auto_detect = self.settings_service.get("auto_detect_src", True)

            self._cleanup_thread('text_worker')
            self.text_worker = TextTranslationWorkerThread(
                clean_text, cursor_pos, self.translate_service,
                target_lang=target_lang, auto_detect=auto_detect
            )
            self.text_worker.finished.connect(self.on_selected_text_translation_finished)
            self.text_worker.start()
        finally:
            self._is_processing_clipboard = False

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, '_drag_pos'):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def position_at_bottom_right(self):
        screen = QGuiApplication.primaryScreen()
        avail_geo = screen.availableGeometry()
        win_w = self.width()
        win_h = self.height()
        x = avail_geo.right() - win_w - 12
        y = avail_geo.bottom() - win_h - 12
        self.setGeometry(x, y, win_w, win_h)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.ActivationChange:
            if not self.isActiveWindow():
                if not QApplication.activeModalWidget():
                    self.hide()
        super().changeEvent(event)

    def setup_shortcuts(self):
        crop_preset = self.settings_service.get("hotkey_preset", "Alt+S")
        sel_preset = self.settings_service.get("selection_translate_hotkey", "Alt+C")

        if hasattr(self, '_shortcut_crop') and self._shortcut_crop:
            try:
                self._shortcut_crop.deleteLater()
            except Exception:
                pass
        if hasattr(self, '_shortcut_sel') and self._shortcut_sel:
            try:
                self._shortcut_sel.deleteLater()
            except Exception:
                pass

        self._shortcut_crop = QShortcut(QKeySequence(crop_preset), self, self.start_selection_safe)
        self._shortcut_sel = QShortcut(QKeySequence(sel_preset), self, self.translate_selected_text_at_cursor)

    def _clear_active_popup(self):
        """Aktif popup nesnesini güvenli şekilde kapatır ve bellekten siler."""
        if self.active_popup is not None:
            try:
                self.active_popup.close()
                self.active_popup.deleteLater()
            except Exception:
                pass
            self.active_popup = None

    def setup_pynput_hotkey(self):
        enable_hotkeys = self.settings_service.get("enable_hotkeys", True)
        crop_preset = self.settings_service.get("hotkey_preset", "Alt+S")
        sel_preset = self.settings_service.get("selection_translate_hotkey", "Alt+C")

        if not hasattr(self, 'hotkey_listener'):
            self.hotkey_listener = HotkeyManager()
            self.hotkey_listener.triggered.connect(self.start_selection_safe)
            self.hotkey_listener.selection_triggered.connect(self.translate_selected_text_at_cursor)

        if enable_hotkeys:
            self.hotkey_listener.start(crop_preset, sel_preset)
        else:
            self.hotkey_listener.stop()

    def start_selection_safe(self):
        self.is_selecting_for_live = False
        self.overlay.start_selection()

    def start_live_selection(self):
        enable_live = self.settings_service.get("enable_live_mode", True)
        if not enable_live:
            show_error_popup(self, "Canlı Mod Kapalı", "Canlı Çeviri özelliği Ayarlar sekmesinden kapatılmıştır.")
            return

        self.is_selecting_for_live = True
        self.overlay.start_selection()

    def setup_tray(self):
        if not hasattr(self, 'tray_manager'):
            self.tray_manager = TrayManager(self)

        self.tray_manager.setup_tray({
            'show': self.show_and_activate,
            'crop': self.start_selection_safe,
            'selection': self.translate_selected_text_at_cursor,
            'live': self.start_live_selection,
            'quit': self.close_app
        })


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
        if self.is_selecting_for_live:
            self.stop_live_mode()
            self.live_overlay = LiveSubtitleOverlay(rect)
            self.live_overlay.paused_toggled.connect(self.on_live_paused_toggled)
            self.live_overlay.closed.connect(self.stop_live_mode)
            self.live_overlay.show()

            interval = self.settings_service.get("live_interval", 2.0)
            skip_unchanged = self.settings_service.get("live_skip_unchanged", True)
            target_lang = self.settings_service.get("target_lang", "tr")
            auto_detect = self.settings_service.get("auto_detect_src", True)
            ocr_engine = self.settings_service.get("ocr_engine", "auto")

            self.live_thread = LiveTranslationWorkerThread(
                rect, self.ocr_service, self.translate_service,
                interval=interval, skip_unchanged=skip_unchanged,
                target_lang=target_lang, auto_detect=auto_detect, ocr_engine=ocr_engine
            )
            self.live_thread.translation_updated.connect(self.on_live_translation_updated)
            self.live_thread.start()

            self.status_label.setText("🔴 Canlı Altyazı Çeviri Modu Aktif.")
            self.status_label.setStyleSheet("color: #00E5FF; font-weight: bold; font-size: 12px;")
            return

        # Normal Tek Tık Ekran Çevirisi
        self.status_label.setText("⏳ Metin okunuyor ve çevriliyor...")
        self.status_label.setStyleSheet("color: #00E5FF; font-weight: bold; font-size: 12px;")

        self._clear_active_popup()
        self.active_popup = LoadingPopup(rect)
        self.active_popup.show()

        target_lang = self.settings_service.get("target_lang", "tr")
        auto_detect = self.settings_service.get("auto_detect_src", True)
        ocr_engine = self.settings_service.get("ocr_engine", "auto")

        self._cleanup_thread('worker_thread')
        self.worker_thread = TranslationWorkerThread(
            rect, physical_coords, self.ocr_service, self.translate_service,
            target_lang=target_lang, auto_detect=auto_detect, ocr_engine=ocr_engine
        )
        self.worker_thread.finished.connect(self.on_translation_finished)
        self.worker_thread.error.connect(self.on_translation_error)
        self.worker_thread.start()

    def on_live_translation_updated(self, ocr_text: str, translated: str, src_lang: str, tgt_lang: str):
        if self.live_overlay:
            self.live_overlay.update_text(translated)

        self.last_translated_text = translated
        self.last_target_lang = tgt_lang
        self.history_service.add_item(ocr_text, translated, src_lang, tgt_lang)
        self.history_tab.load_history()

    def on_live_paused_toggled(self, is_paused: bool):
        if self.live_thread:
            self.live_thread.set_paused(is_paused)

    def stop_live_mode(self):
        if self.live_thread:
            self.live_thread.stop()
            self.live_thread.wait(1000)
            self.live_thread = None

        if self.live_overlay:
            try:
                self.live_overlay.close()
            except Exception:
                pass
            self.live_overlay = None

    def on_translation_finished(self, ocr_text: str, translated: str, src_lang: str, tgt_lang: str, rect: QRect, physical_coords: tuple):
        self._clear_active_popup()
        if not ocr_text.strip():
            self.status_label.setText("⚠️ Okunabilir metin bulunamadı.")
            self.status_label.setStyleSheet("color: #FFCC00; font-weight: bold; font-size: 12px;")
            self.text_display.setText("(Seçilen alanda okunabilir metin bulunamadı)")

            show_error_popup(
                self,
                "Metin Okunamadı",
                "Seçtiğiniz alanda okunabilir herhangi bir metin tespit edilemedi."
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

        # Eğer Kullanıcı Radial (Dairesel) Menüyü Açtıysa SADECE Dairesel Menüyü Göster (Çakışmayı önle)
        if self.settings_service.get("enable_radial_menu", False):
            if hasattr(self, 'radial_menu') and self.radial_menu:
                try:
                    self.radial_menu.close()
                except Exception:
                    pass
            self.radial_menu = RadialMenu()
            self.radial_menu.action_selected.connect(
                lambda act: self.handle_radial_action(act, ocr_text, translated, src_lang, tgt_lang, rect)
            )
            self.radial_menu.show_at_position(rect.center())
            return

        # Varsayılan Akış: In-Place veya Sade Premium Popup Gösterimi
        if self.settings_service.get("enable_in_place", True):
            if self.in_place_overlay is not None:
                try:
                    self.in_place_overlay.close()
                except Exception:
                    pass
            self.in_place_overlay = InPlaceOverlay(rect, translated)
            self.in_place_overlay.show()
        else:
            duration = self.settings_service.get("popup_duration", 0)
            self._clear_active_popup()
            self.active_popup = TranslationPopup(ocr_text, translated, src_lang, tgt_lang, rect, duration_sec=duration)
            self.active_popup.copy_requested.connect(lambda text: safe_set_clipboard(text))
            self.active_popup.speak_requested.connect(lambda text, lang: self.tts_service.speak(text, lang))
            self.active_popup.ai_action_requested.connect(self.on_ai_action_requested)
            self.active_popup.show()

    def handle_radial_action(self, action_key: str, ocr_text: str, translated: str, src_lang: str, tgt_lang: str, rect: QRect):
        """Radial Menü üzerindeki dairesel buton aksiyonlarını yürütür."""
        if action_key == "speak":
            self.tts_service.speak(translated, tgt_lang)
        elif action_key == "copy":
            safe_set_clipboard(translated)
            self.status_label.setText("📋 Çeviri panoya kopyalandı!")
            self.status_label.setStyleSheet("color: #00FF88; font-weight: bold;")
        elif action_key == "ai_explain":
            self.on_ai_action_requested("summarize", ocr_text or translated)
        elif action_key == "vocab":
            self.vocab_service.add_word(ocr_text, translated, src_lang, tgt_lang)
            self.vocab_tab.load_due_cards()
            self.vocab_tab.load_vocab_table()
            self.status_label.setText("🎴 Kelime kartlarına başarıyla eklendi!")
            self.status_label.setStyleSheet("color: #00FF88; font-weight: bold;")
        elif action_key == "pin":
            duration = self.settings_service.get("popup_duration", 0)
            self._clear_active_popup()
            self.active_popup = TranslationPopup(ocr_text, translated, src_lang, tgt_lang, rect, duration_sec=duration)
            if not self.active_popup.is_pinned:
                self.active_popup.toggle_pin()
            self.active_popup.copy_requested.connect(lambda text: safe_set_clipboard(text))
            self.active_popup.speak_requested.connect(lambda text, lang: self.tts_service.speak(text, lang))
            self.active_popup.ai_action_requested.connect(self.on_ai_action_requested)
            self.active_popup.show()

    def on_translation_error(self, error_msg: str):
        self._clear_active_popup()
        self.status_label.setText(f"❌ Hata: {error_msg}")
        self.status_label.setStyleSheet("color: #FF6B6B; font-size: 12px;")
        show_error_popup(self, "Bağlantı / Çeviri Hatası", error_msg)

    def on_selection_cancelled(self):
        self.is_selecting_for_live = False
        self.status_label.setText("Seçim iptal edildi (ESC tuşlandı veya alan çok küçük).")
        self.status_label.setStyleSheet("color: #FF6B6B; font-size: 12px;")

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def close_app(self):
        self.stop_live_mode()
        if hasattr(self, 'hotkey_listener'):
            self.hotkey_listener.stop()
        if self.floating_widget:
            self.floating_widget.close()
        QApplication.quit()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    window = MainWindow()
    window.hide()

    crop_preset = window.settings_service.get("hotkey_preset", "Alt+S")
    sel_preset = window.settings_service.get("selection_translate_hotkey", "Alt+C")

    window.tray_manager.show_message(
        "A.L.P. (Auto Language Parser)",
        f"Uygulama arka planda ve sistem tepsisinde aktif.\nKısayollar: {crop_preset} (Kırp) veya {sel_preset} (Seçili Metin)",
        QSystemTrayIcon.MessageIcon.Information,
        3000
    )

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
