from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QComboBox, QPushButton, QTabWidget, QMessageBox, QFrame
)
from services.settings_service import SettingsService


class SettingsTab(QWidget):
    """
    Stitch 'System Tray Utility - Basitleştirilmiş Üst Menülü Ayarlar' Birebir Görsel Arayüzü.
    Görseldeki renkler, sekmeler, switch'ler, kısayol kutusu ve butonlar 1:1 uygulanmıştır.
    """
    settings_saved = Signal()

    def __init__(self, settings_service: SettingsService):
        super().__init__()
        self.settings_service = settings_service
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # Birebir Stitch Dark Slate Teması
        self.setStyleSheet("""
            QWidget {
                background-color: #081425;
                color: #D8E3FB;
                font-family: 'Inter', 'Segoe UI', sans-serif;
            }

            /* Üst Menü Navigasyon Sekmeleri */
            QTabWidget::pane {
                border: 1px solid #1E2E42;
                background-color: #081425;
                border-radius: 6px;
            }
            QTabBar::tab {
                background-color: #111C2D;
                color: #94A3B8;
                padding: 8px 0px;
                font-weight: 600;
                font-size: 12px;
                min-width: 140px;
                border: none;
                border-bottom: 2px solid transparent;
            }
            QTabBar::tab:selected {
                background-color: #192638;
                color: #7BD0FF;
                border-bottom: 2px solid #7BD0FF;
            }
            QTabBar::tab:hover:!selected {
                background-color: #152031;
                color: #FFFFFF;
            }

            /* Bölüm Başlıkları */
            QLabel#sectionHeader {
                color: #D8E3FB;
                font-size: 11px;
                font-weight: 800;
                letter-spacing: 1px;
            }

            /* Cam Kartlar (Glass Cards) */
            QFrame#settingCard {
                background-color: rgba(25, 38, 56, 0.7);
                border: 1px solid #1E2E42;
                border-radius: 6px;
            }

            /* Switch (CheckBox) Stili */
            QCheckBox#stitchToggle {
                font-size: 13px;
                color: #D8E3FB;
                font-weight: 500;
                spacing: 8px;
            }
            QCheckBox#stitchToggle::indicator {
                width: 32px;
                height: 18px;
                border-radius: 9px;
                background-color: #1E2E42;
            }
            QCheckBox#stitchToggle::indicator:checked {
                background-color: #7BD0FF;
            }

            /* ComboBox Stili */
            QComboBox {
                background-color: #040E1F;
                color: #7BD0FF;
                border: 1px solid #1E2E42;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 12px;
                font-weight: 600;
            }
            QComboBox:hover {
                border-color: #7BD0FF;
            }

            /* İpucu Koyu Kartı */
            QFrame#infoToast {
                background-color: #081828;
                border: 1px solid #1A2B3F;
                border-radius: 6px;
            }

            /* Butonlar */
            QPushButton#btnSave {
                background-color: #7BD0FF;
                color: #00374D;
                font-size: 12px;
                font-weight: 700;
                border-radius: 4px;
                padding: 6px 18px;
                border: none;
            }
            QPushButton#btnSave:hover {
                background-color: #99DCFF;
            }
            QPushButton#btnCancel {
                background-color: transparent;
                color: #94A3B8;
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
                color: #64748B;
                font-size: 11px;
                padding: 6px 8px;
                border: none;
            }
            QPushButton#btnReset:hover {
                color: #94A3B8;
            }
        """)

        # Stitch Sekmeli Yapı
        self.sub_tabs = QTabWidget()

        # ====================================================
        # SEKME 1: ⚙️ Ayarlar (Genel & Kısayol Tuşları)
        # ====================================================
        tab_main_settings = QWidget()
        sec_layout = QVBoxLayout(tab_main_settings)
        sec_layout.setContentsMargins(10, 12, 10, 12)
        sec_layout.setSpacing(10)

        # 1. GENEL AYARLAR
        lbl_gen_hdr = QLabel("GENEL AYARLAR")
        lbl_gen_hdr.setObjectName("sectionHeader")
        sec_layout.addWidget(lbl_gen_hdr)

        # Kart: Başlangıçta çalıştır / Otomatik Kopyalama
        card_gen = QFrame()
        card_gen.setObjectName("settingCard")
        cg_layout = QVBoxLayout(card_gen)
        cg_layout.setContentsMargins(12, 10, 12, 10)
        cg_layout.setSpacing(8)

        self.chk_auto_copy = QCheckBox("Başlangıçta çalıştır (Otomatik Kopyala)")
        self.chk_auto_copy.setObjectName("stitchToggle")
        cg_layout.addWidget(self.chk_auto_copy)

        self.chk_auto_tts = QCheckBox("Çeviriyi Otomatik Sesli Oku (TTS)")
        self.chk_auto_tts.setObjectName("stitchToggle")
        cg_layout.addWidget(self.chk_auto_tts)

        sec_layout.addWidget(card_gen)

        # Ayırıcı İnce Çizgi
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background-color: #1E2E42; max-height: 1px; border: none;")
        sec_layout.addWidget(divider)

        # 2. KISAYOL TUŞLARI
        lbl_hk_hdr = QLabel("KISAYOL TUŞLARI")
        lbl_hk_hdr.setObjectName("sectionHeader")
        sec_layout.addWidget(lbl_hk_hdr)

        lbl_hk_sub = QLabel("Açılış Kısayolu")
        lbl_hk_sub.setStyleSheet("font-size: 11px; color: #94A3B8; font-weight: 500;")
        sec_layout.addWidget(lbl_hk_sub)

        # Kısayol Seçici ComboBox
        self.cmb_hotkey = QComboBox()
        self.cmb_hotkey.addItem("Alt + S  (Önerilen)", "Alt+S")
        self.cmb_hotkey.addItem("F8  (Tek Tuş Kısayolu)", "F8")
        self.cmb_hotkey.addItem("Ctrl + Alt + S", "Ctrl+Alt+S")
        sec_layout.addWidget(self.cmb_hotkey)

        # Bilgi İpucu Kartı (Info Toast)
        info_toast = QFrame()
        info_toast.setObjectName("infoToast")
        it_layout = QHBoxLayout(info_toast)
        it_layout.setContentsMargins(10, 8, 10, 8)
        it_layout.setSpacing(8)

        lbl_info_icon = QLabel("❓")
        lbl_info_icon.setStyleSheet("font-size: 13px; color: #7BD0FF; background: transparent;")
        it_layout.addWidget(lbl_info_icon, alignment=Qt.AlignmentFlag.AlignTop)

        lbl_info_text = QLabel("Kısayolu değiştirmek için kutudan yeni tuş kombinasyonunu seçin ve Kaydet butonuna basın.")
        lbl_info_text.setWordWrap(True)
        lbl_info_text.setStyleSheet("font-size: 11px; color: #94A3B8; line-height: 1.3; background: transparent;")
        it_layout.addWidget(lbl_info_text, stretch=1)

        sec_layout.addWidget(info_toast)

        sec_layout.addStretch()
        self.sub_tabs.addTab(tab_main_settings, "⚙️ Ayarlar")

        # ====================================================
        # SEKME 2: 🌐 Dil & Görünüm
        # ====================================================
        tab_lang_settings = QWidget()
        lang_layout = QVBoxLayout(tab_lang_settings)
        lang_layout.setContentsMargins(10, 12, 10, 12)
        lang_layout.setSpacing(10)

        lbl_lang_hdr = QLabel("POPUP & GÖRÜNÜM TERCIHLERI")
        lbl_lang_hdr.setObjectName("sectionHeader")
        lang_layout.addWidget(lbl_lang_hdr)

        card_lang = QFrame()
        card_lang.setObjectName("settingCard")
        cl_layout = QVBoxLayout(card_lang)
        cl_layout.setContentsMargins(12, 10, 12, 10)
        cl_layout.setSpacing(8)

        lbl_dur = QLabel("Popup Kalma Süresi:")
        lbl_dur.setStyleSheet("font-size: 12px; font-weight: 600; color: #D8E3FB;")
        cl_layout.addWidget(lbl_dur)

        self.cmb_duration = QComboBox()
        self.cmb_duration.addItem("Tıklayana Kadar Kapanmasın (Varsayılan)", 0)
        self.cmb_duration.addItem("3 Saniye", 3)
        self.cmb_duration.addItem("5 Saniye", 5)
        self.cmb_duration.addItem("10 Saniye", 10)
        cl_layout.addWidget(self.cmb_duration)

        lang_layout.addWidget(card_lang)
        lang_layout.addStretch()

        self.sub_tabs.addTab(tab_lang_settings, "🌐 Dil")

        main_layout.addWidget(self.sub_tabs)

        # Stitch Alt İşlem Çubuğu (Footer Actions)
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
        msg.setStyleSheet("background-color: #081425; color: #D8E3FB; font-size: 13px;")
        msg.exec()

    def reset_to_defaults(self):
        self.settings_service.reset_defaults()
        self.load_settings()
        self.settings_saved.emit()

        msg = QMessageBox(self)
        msg.setWindowTitle("Varsayılanlara Sıfırlandı")
        msg.setText("Tüm ayarlar fabrika varsayılanlarına sıfırlandı!")
        msg.setStyleSheet("background-color: #081425; color: #D8E3FB; font-size: 13px;")
        msg.exec()
