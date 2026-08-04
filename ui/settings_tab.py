from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QKeySequence
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QComboBox, QPushButton, QTabWidget, QMessageBox, QFrame,
    QDoubleSpinBox, QSlider
)
from services.settings_service import SettingsService
from services.translate_service import TranslationService


class HotkeyRecordWidget(QPushButton):
    """
    Kullanıcının klavyedeki herhangi bir tuş kombinasyonunu (Örn: Ctrl+Alt+X, Alt+Z, F10)
    basarak canlı kaydetmesini sağlayan interaktif kısayol kaydedici butonu.
    """
    hotkey_changed = Signal(str)

    def __init__(self, current_hotkey: str = "Alt+S"):
        super().__init__()
        self.current_hotkey = current_hotkey
        self.is_recording = False
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_button_text()

    def update_button_text(self):
        if self.is_recording:
            self.setText("⌨️ Tuşlara Basın... (İptal için ESC)")
            self.setStyleSheet("""
                QPushButton {
                    background-color: #0078D4;
                    color: #FFFFFF;
                    border: 2px solid #00E5FF;
                    border-radius: 6px;
                    padding: 7px 12px;
                    font-weight: 700;
                    font-size: 12px;
                }
            """)
        else:
            self.setText(f"🎹 Kısayol: {self.current_hotkey}  (Değiştirmek İçin Tıklayın)")
            self.setStyleSheet("""
                QPushButton {
                    background-color: #18181B;
                    color: #F4F4F5;
                    border: 1px solid #3F3F46;
                    border-radius: 6px;
                    padding: 7px 12px;
                    font-weight: 600;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #27272A;
                    border-color: #0078D4;
                }
            """)

    def mousePressEvent(self, event):
        if not self.is_recording:
            self.is_recording = True
            self.update_button_text()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if not self.is_recording:
            super().keyPressEvent(event)
            return

        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.is_recording = False
            self.update_button_text()
            return

        if key in (Qt.Key.Key_Control, Qt.Key.Key_Alt, Qt.Key.Key_Shift, Qt.Key.Key_Meta):
            return

        modifiers = event.modifiers()
        parts = []
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            parts.append("Ctrl")
        if modifiers & Qt.KeyboardModifier.AltModifier:
            parts.append("Alt")
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            parts.append("Shift")

        key_str = QKeySequence(key).toString()
        if key_str:
            parts.append(key_str)

        new_hotkey = "+".join(parts)
        if new_hotkey:
            self.current_hotkey = new_hotkey
            self.hotkey_changed.emit(new_hotkey)

        self.is_recording = False
        self.update_button_text()


class SettingsTab(QWidget):
    """
    A.L.P. gelişmiş özelliklerinin tümünü açma/kapatma (toggle switch) ve özelleştirme ayarları.
    """
    settings_saved = Signal()

    def __init__(self, settings_service: SettingsService):
        super().__init__()
        self.settings_service = settings_service
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Premium Obsidian Zinc Teması
        self.setStyleSheet("""
            QWidget {
                background-color: #09090B;
                color: #F4F4F5;
                font-family: 'Segoe UI', -apple-system, sans-serif;
            }

            QTabWidget::pane {
                border: 1px solid #27272A;
                background-color: #09090B;
                border-radius: 6px;
            }
            QTabBar::tab {
                background-color: transparent;
                color: #A1A1AA;
                padding: 6px 12px;
                font-weight: 600;
                font-size: 11px;
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

            QLabel#sectionHeader {
                color: #A1A1AA;
                font-size: 11px;
                font-weight: 800;
                letter-spacing: 0.5px;
            }

            QFrame#settingCard {
                background-color: #18181B;
                border: 1px solid #27272A;
                border-radius: 8px;
            }

            QCheckBox#stitchToggle {
                font-size: 12px;
                color: #F4F4F5;
                font-weight: 500;
                spacing: 8px;
            }
            QCheckBox#stitchToggle::indicator {
                width: 32px;
                height: 18px;
                border-radius: 9px;
                background-color: #27272A;
            }
            QCheckBox#stitchToggle::indicator:checked {
                background-color: #0078D4;
            }

            QComboBox, QDoubleSpinBox {
                background-color: #09090B;
                color: #F4F4F5;
                border: 1px solid #27272A;
                border-radius: 6px;
                padding: 5px 10px;
                font-size: 12px;
                font-weight: 600;
            }
            QComboBox:hover, QDoubleSpinBox:hover {
                border-color: #0078D4;
            }

            QSlider::groove:horizontal {
                border: none;
                height: 4px;
                background: #27272A;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #0078D4;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #FFFFFF;
                border: 1px solid #0078D4;
                width: 14px;
                height: 14px;
                margin-top: -5px;
                margin-bottom: -5px;
                border-radius: 7px;
            }

            QFrame#infoToast {
                background-color: #18181B;
                border: 1px solid #27272A;
                border-radius: 8px;
            }

            QPushButton#btnSave {
                background-color: #0078D4;
                color: #FFFFFF;
                font-size: 12px;
                font-weight: 700;
                border-radius: 6px;
                padding: 6px 18px;
                border: none;
            }
            QPushButton#btnSave:hover {
                background-color: #106EBE;
            }
            QPushButton#btnCancel {
                background-color: transparent;
                color: #A1A1AA;
                font-size: 12px;
                font-weight: 600;
                padding: 6px 12px;
                border: none;
            }
            QPushButton#btnCancel:hover {
                color: #FFFFFF;
            }
            QPushButton#btnReset {
                background-color: transparent;
                color: #71717A;
                font-size: 11px;
                padding: 6px 8px;
                border: none;
            }
            QPushButton#btnReset:hover {
                color: #A1A1AA;
            }
        """)

        self.sub_tabs = QTabWidget()

        # ====================================================
        # SEKME 1: ⚙️ Genel & Kısayollar
        # ====================================================
        tab_gen = QWidget()
        gen_layout = QVBoxLayout(tab_gen)
        gen_layout.setContentsMargins(10, 10, 10, 10)
        gen_layout.setSpacing(8)

        lbl_gen_hdr = QLabel("GENEL & KISAYOL AYARLARI")
        lbl_gen_hdr.setObjectName("sectionHeader")
        gen_layout.addWidget(lbl_gen_hdr)

        card_gen = QFrame()
        card_gen.setObjectName("settingCard")
        cg_layout = QVBoxLayout(card_gen)
        cg_layout.setContentsMargins(12, 10, 12, 10)
        cg_layout.setSpacing(8)

        self.chk_auto_copy = QCheckBox("Çeviriyi Otomatik Panoya Kopyala")
        self.chk_auto_copy.setObjectName("stitchToggle")
        cg_layout.addWidget(self.chk_auto_copy)

        self.chk_auto_tts = QCheckBox("Çeviriyi Otomatik Sesli Oku (TTS)")
        self.chk_auto_tts.setObjectName("stitchToggle")
        cg_layout.addWidget(self.chk_auto_tts)

        self.chk_enable_hotkeys = QCheckBox("Global Klavye Kısayollarını Etkinleştir (Alt+S / F8)")
        self.chk_enable_hotkeys.setObjectName("stitchToggle")
        cg_layout.addWidget(self.chk_enable_hotkeys)

        self.chk_enable_selection = QCheckBox("Seçili Metin Çevirisini Etkinleştir (Metni seçip kısayola bas)")
        self.chk_enable_selection.setObjectName("stitchToggle")
        cg_layout.addWidget(self.chk_enable_selection)

        self.chk_auto_clipboard = QCheckBox("Panoya Kopyalanan Metinleri Otomatik Çevir")
        self.chk_auto_clipboard.setObjectName("stitchToggle")
        cg_layout.addWidget(self.chk_auto_clipboard)

        gen_layout.addWidget(card_gen)

        lbl_hk_sub = QLabel("Ekran Seçim Kısayolu:")
        lbl_hk_sub.setStyleSheet("font-size: 11px; color: #A1A1AA; font-weight: 600;")
        gen_layout.addWidget(lbl_hk_sub)

        self.btn_hotkey_crop = HotkeyRecordWidget(current_hotkey="Alt+S")
        gen_layout.addWidget(self.btn_hotkey_crop)

        lbl_sel_hk_sub = QLabel("Seçili Metni Çevirme Kısayolu:")
        lbl_sel_hk_sub.setStyleSheet("font-size: 11px; color: #A1A1AA; font-weight: 600; margin-top: 4px;")
        gen_layout.addWidget(lbl_sel_hk_sub)

        self.btn_hotkey_selection = HotkeyRecordWidget(current_hotkey="Alt+C")
        gen_layout.addWidget(self.btn_hotkey_selection)

        gen_layout.addStretch()
        self.sub_tabs.addTab(tab_gen, "⚙️ Genel")

        # ====================================================
        # SEKME 2: 📺 Canlı Çeviri Modu
        # ====================================================
        tab_live = QWidget()
        live_layout = QVBoxLayout(tab_live)
        live_layout.setContentsMargins(10, 10, 10, 10)
        live_layout.setSpacing(8)

        lbl_live_hdr = QLabel("CANLI CHAT / ALTYAZI ÇEVİRİ AYARLARI")
        lbl_live_hdr.setObjectName("sectionHeader")
        live_layout.addWidget(lbl_live_hdr)

        card_live = QFrame()
        card_live.setObjectName("settingCard")
        cl_layout = QVBoxLayout(card_live)
        cl_layout.setContentsMargins(12, 10, 12, 10)
        cl_layout.setSpacing(10)

        self.chk_enable_live = QCheckBox("Canlı Çeviri Özelliğini Etkinleştir")
        self.chk_enable_live.setObjectName("stitchToggle")
        cl_layout.addWidget(self.chk_enable_live)

        self.chk_live_skip = QCheckBox("Görüntü Değişmediyse OCR/Çeviri Yapma (Kaynak Tasarrufu)")
        self.chk_live_skip.setObjectName("stitchToggle")
        cl_layout.addWidget(self.chk_live_skip)

        h_spin = QHBoxLayout()
        lbl_interval = QLabel("Tarama Sıklığı (Saniye):")
        lbl_interval.setStyleSheet("font-size: 12px; font-weight: 600; color: #F4F4F5;")
        h_spin.addWidget(lbl_interval)

        self.spin_interval = QDoubleSpinBox()
        self.spin_interval.setRange(0.5, 10.0)
        self.spin_interval.setSingleStep(0.5)
        self.spin_interval.setSuffix(" sn")
        h_spin.addWidget(self.spin_interval)
        cl_layout.addLayout(h_spin)

        live_layout.addWidget(card_live)
        live_layout.addStretch()
        self.sub_tabs.addTab(tab_live, "📺 Canlı Mod")

        # ====================================================
        # SEKME 3: 🧲 Yüzen Araç Çubuğu
        # ====================================================
        tab_float = QWidget()
        float_layout = QVBoxLayout(tab_float)
        float_layout.setContentsMargins(10, 10, 10, 10)
        float_layout.setSpacing(8)

        lbl_float_hdr = QLabel("MASAÜSTÜ YÜZEN BAR (FLOATING WIDGET)")
        lbl_float_hdr.setObjectName("sectionHeader")
        float_layout.addWidget(lbl_float_hdr)

        card_float = QFrame()
        card_float.setObjectName("settingCard")
        cfl_layout = QVBoxLayout(card_float)
        cfl_layout.setContentsMargins(12, 10, 12, 10)
        cfl_layout.setSpacing(10)

        self.chk_show_floating = QCheckBox("Masaüstü Yüzen Araç Çubuğunu Göster")
        self.chk_show_floating.setObjectName("stitchToggle")
        cfl_layout.addWidget(self.chk_show_floating)

        h_slider = QHBoxLayout()
        lbl_opac = QLabel("Saydamlık Seviyesi:")
        lbl_opac.setStyleSheet("font-size: 12px; font-weight: 600; color: #F4F4F5;")
        h_slider.addWidget(lbl_opac)

        self.slider_opacity = QSlider(Qt.Orientation.Horizontal)
        self.slider_opacity.setRange(30, 100)
        self.lbl_opac_val = QLabel("%90")
        self.lbl_opac_val.setStyleSheet("font-weight: bold; color: #0078D4;")
        self.slider_opacity.valueChanged.connect(lambda v: self.lbl_opac_val.setText(f"%{v}"))

        h_slider.addWidget(self.slider_opacity)
        h_slider.addWidget(self.lbl_opac_val)
        cfl_layout.addLayout(h_slider)

        float_layout.addWidget(card_float)
        float_layout.addStretch()
        self.sub_tabs.addTab(tab_float, "🧲 Yüzen Bar")

        # ====================================================
        # SEKME 4: 🌐 Dil & Çeviri
        # ====================================================
        tab_lang = QWidget()
        lang_layout = QVBoxLayout(tab_lang)
        lang_layout.setContentsMargins(10, 10, 10, 10)
        lang_layout.setSpacing(8)

        lbl_lang_hdr = QLabel("DİL & ÇEVİRİ TERCIHLERİ")
        lbl_lang_hdr.setObjectName("sectionHeader")
        lang_layout.addWidget(lbl_lang_hdr)

        card_lang = QFrame()
        card_lang.setObjectName("settingCard")
        clang_layout = QVBoxLayout(card_lang)
        clang_layout.setContentsMargins(12, 10, 12, 10)
        clang_layout.setSpacing(10)

        self.chk_auto_detect = QCheckBox("Otomatik Dil Algılama & Yön Değiştirme (TR ↔ EN)")
        self.chk_auto_detect.setObjectName("stitchToggle")
        clang_layout.addWidget(self.chk_auto_detect)

        lbl_target = QLabel("Varsayılan Hedef Dil:")
        lbl_target.setStyleSheet("font-size: 12px; font-weight: 600; color: #F4F4F5;")
        clang_layout.addWidget(lbl_target)

        self.cmb_target_lang = QComboBox()
        for code, name in TranslationService.SUPPORTED_LANGUAGES.items():
            self.cmb_target_lang.addItem(f"{name} ({code.upper()})", code)
        clang_layout.addWidget(self.cmb_target_lang)

        lbl_dur = QLabel("Popup Görünme Süresi:")
        lbl_dur.setStyleSheet("font-size: 12px; font-weight: 600; color: #F4F4F5; margin-top: 4px;")
        clang_layout.addWidget(lbl_dur)

        self.cmb_duration = QComboBox()
        self.cmb_duration.addItem("Tıklayana Kadar Kapanmasın (Varsayılan)", 0)
        self.cmb_duration.addItem("3 Saniye", 3)
        self.cmb_duration.addItem("5 Saniye", 5)
        self.cmb_duration.addItem("10 Saniye", 10)
        clang_layout.addWidget(self.cmb_duration)

        lbl_ocr_eng = QLabel("OCR Motor Seçimi:")
        lbl_ocr_eng.setStyleSheet("font-size: 12px; font-weight: 600; color: #F4F4F5; margin-top: 4px;")
        clang_layout.addWidget(lbl_ocr_eng)

        self.cmb_ocr_engine = QComboBox()
        self.cmb_ocr_engine.addItem("⚡ Otomatik (WinOCR ➔ RapidOCR Akıllı Geçiş)", "auto")
        self.cmb_ocr_engine.addItem("🚀 Windows 11 Native WinOCR (0-RAM & Ultra Hız)", "winocr")
        self.cmb_ocr_engine.addItem("🔍 RapidOCR / Native PaddleOCR Engine", "rapid_paddle")
        clang_layout.addWidget(self.cmb_ocr_engine)

        lang_layout.addWidget(card_lang)
        lang_layout.addStretch()
        self.sub_tabs.addTab(tab_lang, "🌐 Dil & OCR")

        # ====================================================
        # SEKME 5: 🚀 Next-Gen Özellikler
        # ====================================================
        tab_nextgen = QWidget()
        ng_layout = QVBoxLayout(tab_nextgen)
        ng_layout.setContentsMargins(10, 10, 10, 10)
        ng_layout.setSpacing(8)

        lbl_ng_hdr = QLabel("ULTRA-PREMIUM NEXT-GEN MODÜLLER")
        lbl_ng_hdr.setObjectName("sectionHeader")
        ng_layout.addWidget(lbl_ng_hdr)

        card_ng = QFrame()
        card_ng.setObjectName("settingCard")
        cng_layout = QVBoxLayout(card_ng)
        cng_layout.setContentsMargins(12, 10, 12, 10)
        cng_layout.setSpacing(10)

        self.chk_enable_in_place = QCheckBox("🖼️ Metnin Yerinde Değiştirilmesi (In-Place Overwrite)")
        self.chk_enable_in_place.setObjectName("stitchToggle")
        cng_layout.addWidget(self.chk_enable_in_place)

        self.chk_enable_context_ai = QCheckBox("🧠 Akıllı Bağlam & Jargon Çevirisi (Yazılım / Oyun)")
        self.chk_enable_context_ai.setObjectName("stitchToggle")
        cng_layout.addWidget(self.chk_enable_context_ai)

        self.chk_enable_hover_dict = QCheckBox("🖱️ Fare Sabitleyince Anında Sözlük (0.4s Hover)")
        self.chk_enable_hover_dict.setObjectName("stitchToggle")
        cng_layout.addWidget(self.chk_enable_hover_dict)

        self.chk_enable_vocab_builder = QCheckBox("🎓 Kelime Öğrenme & Anki Hafıza Kartları")
        self.chk_enable_vocab_builder.setObjectName("stitchToggle")
        cng_layout.addWidget(self.chk_enable_vocab_builder)

        self.chk_enable_radial_menu = QCheckBox("⭕ Dairesel Aksiyon Menüsü (Radial Quick Menu)")
        self.chk_enable_radial_menu.setObjectName("stitchToggle")
        cng_layout.addWidget(self.chk_enable_radial_menu)

        ng_layout.addWidget(card_ng)
        ng_layout.addStretch()
        self.sub_tabs.addTab(tab_nextgen, "🚀 Next-Gen")

        main_layout.addWidget(self.sub_tabs)

        # Alt İşlem Çubuğu
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 4, 0, 0)
        footer_layout.setSpacing(6)

        btn_reset = QPushButton("🔄 Sıfırla")
        btn_reset.setObjectName("btnReset")
        btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reset.clicked.connect(self.reset_to_defaults)
        footer_layout.addWidget(btn_reset)

        footer_layout.addStretch()

        btn_cancel = QPushButton("İptal")
        btn_cancel.setObjectName("btnCancel")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.clicked.connect(self.load_settings)
        footer_layout.addWidget(btn_cancel)

        btn_save = QPushButton("Kaydet")
        btn_save.setObjectName("btnSave")
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.clicked.connect(self.save_settings)
        footer_layout.addWidget(btn_save)

        main_layout.addLayout(footer_layout)

    def load_settings(self):
        auto_copy = self.settings_service.get("auto_copy", True)
        auto_tts = self.settings_service.get("auto_tts", False)
        duration = self.settings_service.get("popup_duration", 0)
        hotkey = self.settings_service.get("hotkey_preset", "Alt+S")

        enable_live = self.settings_service.get("enable_live_mode", True)
        live_interval = self.settings_service.get("live_interval", 2.0)
        live_skip = self.settings_service.get("live_skip_unchanged", True)

        show_floating = self.settings_service.get("show_floating_widget", True)
        floating_opacity = self.settings_service.get("floating_opacity", 90)

        enable_hotkeys = self.settings_service.get("enable_hotkeys", True)
        target_lang = self.settings_service.get("target_lang", "tr")
        auto_detect = self.settings_service.get("auto_detect_src", True)

        enable_selection = self.settings_service.get("enable_selection_translation", True)
        auto_clipboard = self.settings_service.get("auto_clipboard_translate", False)
        selection_hotkey = self.settings_service.get("selection_translate_hotkey", "Alt+C")

        self.chk_auto_copy.setChecked(auto_copy)
        self.chk_auto_tts.setChecked(auto_tts)
        self.chk_enable_hotkeys.setChecked(enable_hotkeys)
        self.chk_enable_selection.setChecked(enable_selection)
        self.chk_auto_clipboard.setChecked(auto_clipboard)

        self.chk_enable_live.setChecked(enable_live)
        self.chk_live_skip.setChecked(live_skip)
        self.spin_interval.setValue(live_interval)

        self.chk_show_floating.setChecked(show_floating)
        self.slider_opacity.setValue(floating_opacity)
        self.lbl_opac_val.setText(f"%{floating_opacity}")

        self.chk_auto_detect.setChecked(auto_detect)

        enable_in_place = self.settings_service.get("enable_in_place", True)
        enable_context_ai = self.settings_service.get("enable_context_ai", True)
        enable_hover_dict = self.settings_service.get("enable_hover_dict", True)
        enable_vocab_builder = self.settings_service.get("enable_vocab_builder", True)
        enable_radial_menu = self.settings_service.get("enable_radial_menu", True)

        self.chk_enable_in_place.setChecked(enable_in_place)
        self.chk_enable_context_ai.setChecked(enable_context_ai)
        self.chk_enable_hover_dict.setChecked(enable_hover_dict)
        self.chk_enable_vocab_builder.setChecked(enable_vocab_builder)
        self.chk_enable_radial_menu.setChecked(enable_radial_menu)

        idx_dur = self.cmb_duration.findData(duration)
        if idx_dur >= 0:
            self.cmb_duration.setCurrentIndex(idx_dur)

        self.btn_hotkey_crop.current_hotkey = hotkey
        self.btn_hotkey_crop.update_button_text()

        self.btn_hotkey_selection.current_hotkey = selection_hotkey
        self.btn_hotkey_selection.update_button_text()

        idx_target = self.cmb_target_lang.findData(target_lang)
        if idx_target >= 0:
            self.cmb_target_lang.setCurrentIndex(idx_target)

        ocr_engine = self.settings_service.get("ocr_engine", "auto")
        idx_ocr = self.cmb_ocr_engine.findData(ocr_engine)
        if idx_ocr >= 0:
            self.cmb_ocr_engine.setCurrentIndex(idx_ocr)

    def save_settings(self):
        self.settings_service.set("auto_copy", self.chk_auto_copy.isChecked())
        self.settings_service.set("auto_tts", self.chk_auto_tts.isChecked())
        self.settings_service.set("enable_hotkeys", self.chk_enable_hotkeys.isChecked())
        self.settings_service.set("enable_in_place", self.chk_enable_in_place.isChecked())
        self.settings_service.set("enable_context_ai", self.chk_enable_context_ai.isChecked())
        self.settings_service.set("enable_hover_dict", self.chk_enable_hover_dict.isChecked())
        self.settings_service.set("enable_vocab_builder", self.chk_enable_vocab_builder.isChecked())
        self.settings_service.set("enable_radial_menu", self.chk_enable_radial_menu.isChecked())
        self.settings_service.set("hotkey_preset", self.btn_hotkey_crop.current_hotkey)

        self.settings_service.set("enable_selection_translation", self.chk_enable_selection.isChecked())
        self.settings_service.set("auto_clipboard_translate", self.chk_auto_clipboard.isChecked())
        self.settings_service.set("selection_translate_hotkey", self.btn_hotkey_selection.current_hotkey)

        self.settings_service.set("enable_live_mode", self.chk_enable_live.isChecked())
        self.settings_service.set("live_interval", self.spin_interval.value())
        self.settings_service.set("live_skip_unchanged", self.chk_live_skip.isChecked())

        self.settings_service.set("show_floating_widget", self.chk_show_floating.isChecked())
        self.settings_service.set("floating_opacity", self.slider_opacity.value())

        self.settings_service.set("auto_detect_src", self.chk_auto_detect.isChecked())
        self.settings_service.set("target_lang", self.cmb_target_lang.currentData())
        self.settings_service.set("popup_duration", self.cmb_duration.currentData())
        self.settings_service.set("ocr_engine", self.cmb_ocr_engine.currentData())

        self.settings_saved.emit()

        msg = QMessageBox(self)
        msg.setWindowTitle("Ayarlar Kaydedildi")
        msg.setText("Tercihleriniz başarıyla kaydedildi!")
        msg.setStyleSheet("background-color: #18181B; color: #F4F4F5; font-size: 13px;")
        msg.exec()

    def reset_to_defaults(self):
        self.settings_service.reset_defaults()
        self.load_settings()
        self.settings_saved.emit()

        msg = QMessageBox(self)
        msg.setWindowTitle("Varsayılanlara Sıfırlandı")
        msg.setText("Tüm ayarlar fabrika varsayılanlarına sıfırlandı!")
        msg.setStyleSheet("background-color: #18181B; color: #F4F4F5; font-size: 13px;")
        msg.exec()
