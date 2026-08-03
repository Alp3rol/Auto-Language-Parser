from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QComboBox, QPushButton, QTabWidget, QMessageBox
)
from services.settings_service import SettingsService


class SettingCard(QWidget):
    """Stitch System Tray Utility tasarımına uygun basitleştirilmiş ayar kartı bileşeni."""
    def __init__(self, title: str, subtitle: str, control_widget: QWidget):
        super().__init__()
        self.setObjectName("settingCard")
        self.setStyleSheet("""
            QWidget#settingCard {
                background-color: #1E1E22;
                border: 1px solid #2D2D35;
                border-radius: 8px;
            }
            QWidget#settingCard:hover {
                border: 1px solid #0078D4;
            }
            QLabel#cardTitle {
                color: #FFFFFF;
                font-weight: 600;
                font-size: 13px;
            }
            QLabel#cardSubtitle {
                color: #A1A1AA;
                font-size: 11px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)

        # Sol taraf: Başlık ve Açıklama
        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        lbl_title = QLabel(title)
        lbl_title.setObjectName("cardTitle")
        text_layout.addWidget(lbl_title)

        if subtitle:
            lbl_sub = QLabel(subtitle)
            lbl_sub.setObjectName("cardSubtitle")
            lbl_sub.setWordWrap(True)
            text_layout.addWidget(lbl_sub)

        layout.addWidget(text_container, stretch=1)

        # Sağ taraf: Kontrol Bileşeni (CheckBox, ComboBox vb.)
        layout.addWidget(control_widget, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)


class SettingsTab(QWidget):
    """
    Stitch 'System Tray Utility - Basitleştirilmiş Üst Menülü Ayarlar' Tasarımı.
    - Üst Menü / Sekme Gezintisi (Segmented Header Navigation)
    - Basitleştirilmiş Kurumsal Koyu Kartlar
    - Alt İşlem Çubuğu (Kaydet & Sıfırla)
    """
    settings_saved = Signal()

    def __init__(self, settings_service: SettingsService):
        super().__init__()
        self.settings_service = settings_service
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        self.setStyleSheet("""
            QWidget {
                color: #FFFFFF;
                font-family: 'Segoe UI', -apple-system, sans-serif;
            }
            QTabWidget::pane {
                border: 1px solid #2D2D35;
                background-color: #141416;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #1E1E22;
                color: #A1A1AA;
                padding: 7px 14px;
                font-weight: 600;
                font-size: 11px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 3px;
                border: 1px solid #2D2D35;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background-color: #0078D4;
                color: #FFFFFF;
                border-color: #0078D4;
            }
            QTabBar::tab:hover:!selected {
                background-color: #2D2D35;
                color: #FFFFFF;
            }
            QCheckBox {
                font-size: 12px;
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 1px solid #3F3F46;
                background-color: #27272A;
            }
            QCheckBox::indicator:checked {
                background-color: #0078D4;
                border-color: #0078D4;
            }
            QComboBox {
                background-color: #27272A;
                color: #FFFFFF;
                border: 1px solid #3F3F46;
                border-radius: 6px;
                padding: 5px 10px;
                font-size: 12px;
                min-width: 160px;
            }
            QComboBox:hover {
                border-color: #0078D4;
            }
            QPushButton#btnSave {
                background-color: #0078D4;
                color: white;
                font-size: 12px;
                font-weight: bold;
                border-radius: 6px;
                padding: 8px 16px;
                border: none;
            }
            QPushButton#btnSave:hover {
                background-color: #106EBE;
            }
            QPushButton#btnReset {
                background-color: #27272A;
                color: #A1A1AA;
                font-size: 12px;
                font-weight: 600;
                border-radius: 6px;
                padding: 8px 16px;
                border: 1px solid #3F3F46;
            }
            QPushButton#btnReset:hover {
                background-color: #3F3F46;
                color: #FFFFFF;
            }
        """)

        # Üst Başlık
        header_lbl = QLabel("⚙️ Basitleştirilmiş Sistem Ayarları")
        header_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        main_layout.addWidget(header_lbl)

        # Stitch Üst Menü Sekmeleri (Segmented Top Header)
        self.sub_tabs = QTabWidget()

        # ----------------------------------------------------
        # SEKME 1: ⚙️ Genel Davranışlar
        # ----------------------------------------------------
        tab_general = QWidget()
        gen_layout = QVBoxLayout(tab_general)
        gen_layout.setContentsMargins(10, 10, 10, 10)
        gen_layout.setSpacing(10)

        # Kart 1: Otomatik Kopyala
        self.chk_auto_copy = QCheckBox("Aktif")
        card_copy = SettingCard(
            "📋 Otomatik Panoya Kopyalama",
            "Ekran seçimi çevrildiğinde sonucu doğrudan panoya kopyalar.",
            self.chk_auto_copy
        )
        gen_layout.addWidget(card_copy)

        # Kart 2: Otomatik TTS
        self.chk_auto_tts = QCheckBox("Aktif")
        card_tts = SettingCard(
            "🔊 Otomatik Sesli Okuma (TTS)",
            "Çeviri tamamlandığında çevrilen metni otomatik olarak seslendirir.",
            self.chk_auto_tts
        )
        gen_layout.addWidget(card_tts)

        gen_layout.addStretch()
        self.sub_tabs.addTab(tab_general, "⚙️ Genel")

        # ----------------------------------------------------
        # SEKME 2: 🖥️ Popup & Görünüm
        # ----------------------------------------------------
        tab_popup = QWidget()
        pop_layout = QVBoxLayout(tab_popup)
        pop_layout.setContentsMargins(10, 10, 10, 10)
        pop_layout.setSpacing(10)

        # Kart 3: Popup Süresi
        self.cmb_duration = QComboBox()
        self.cmb_duration.addItem("Tıklayana Kadar Kapanmasın (Varsayılan)", 0)
        self.cmb_duration.addItem("3 Saniye", 3)
        self.cmb_duration.addItem("5 Saniye", 5)
        self.cmb_duration.addItem("10 Saniye", 10)

        card_dur = SettingCard(
            "⏳ Çeviri Katmanı Ekranda Kalma Süresi",
            "Çeviri kutusunun ekran üzerinde açık kalacağı zamanlayıcı tercihi.",
            self.cmb_duration
        )
        pop_layout.addWidget(card_dur)

        pop_layout.addStretch()
        self.sub_tabs.addTab(tab_popup, "🖥️ Popup & Görünüm")

        # ----------------------------------------------------
        # SEKME 3: ⌨️ Kısayollar & Motor
        # ----------------------------------------------------
        tab_hotkeys = QWidget()
        hk_layout = QVBoxLayout(tab_hotkeys)
        hk_layout.setContentsMargins(10, 10, 10, 10)
        hk_layout.setSpacing(10)

        # Kart 4: Kısayollar
        self.cmb_hotkey = QComboBox()
        self.cmb_hotkey.addItem("Alt + S (Varsayılan & Önerilen)", "Alt+S")
        self.cmb_hotkey.addItem("F8 (Tek Tuş Kısayolu)", "F8")
        self.cmb_hotkey.addItem("Ctrl + Alt + S", "Ctrl+Alt+S")

        card_hk = SettingCard(
            "⌨️ Global Ekran Seçim Kısayolu",
            "Ekran çevirici seçim katmanını başlatan sistem geneli tuş kombinasyonu.",
            self.cmb_hotkey
        )
        hk_layout.addWidget(card_hk)

        hk_layout.addStretch()
        self.sub_tabs.addTab(tab_hotkeys, "⌨️ Kısayollar")

        main_layout.addWidget(self.sub_tabs)

        # Alt İşlem Çubuğu (Action Bar: Kaydet & Sıfırla)
        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(0, 5, 0, 0)

        btn_reset = QPushButton("🔄 Varsayılanlara Sıfırla")
        btn_reset.setObjectName("btnReset")
        btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reset.clicked.connect(self.reset_to_defaults)
        action_layout.addWidget(btn_reset)

        action_layout.addStretch()

        btn_save = QPushButton("💾 Ayarları Kaydet")
        btn_save.setObjectName("btnSave")
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.clicked.connect(self.save_settings)
        action_layout.addWidget(btn_save)

        main_layout.addLayout(action_layout)

    def load_settings(self):
        auto_copy = self.settings_service.get("auto_copy", True)
        auto_tts = self.settings_service.get("auto_tts", False)
        duration = self.settings_service.get("popup_duration", 0)
        hotkey = self.settings_service.get("hotkey_preset", "Alt+S")

        self.chk_auto_copy.setChecked(auto_copy)
        self.chk_auto_tts.setChecked(auto_tts)

        idx_dur = self.cmb_duration.findData(duration)
        if idx_dur >= 0:
            self.cmb_duration.setCurrentIndex(idx_dur)

        idx_hk = self.cmb_hotkey.findData(hotkey)
        if idx_hk >= 0:
            self.cmb_hotkey.setCurrentIndex(idx_hk)

    def save_settings(self):
        self.settings_service.set("auto_copy", self.chk_auto_copy.isChecked())
        self.settings_service.set("auto_tts", self.chk_auto_tts.isChecked())
        self.settings_service.set("popup_duration", self.cmb_duration.currentData())
        self.settings_service.set("hotkey_preset", self.cmb_hotkey.currentData())

        self.settings_saved.emit()

        msg = QMessageBox(self)
        msg.setWindowTitle("Ayarlar Kaydedildi")
        msg.setText("Tercihleriniz başarıyla kaydedildi!")
        msg.setStyleSheet("background-color: #252526; color: #FFFFFF; font-size: 13px;")
        msg.exec()

    def reset_to_defaults(self):
        self.settings_service.reset_defaults()
        self.load_settings()
        self.settings_saved.emit()

        msg = QMessageBox(self)
        msg.setWindowTitle("Varsayılanlara Sıfırlandı")
        msg.setText("Tüm ayarlar fabrika varsayılanlarına sıfırlandı!")
        msg.setStyleSheet("background-color: #252526; color: #FFFFFF; font-size: 13px;")
        msg.exec()
