from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QComboBox, QPushButton, QGroupBox, QMessageBox
)
from services.settings_service import SettingsService


class SettingsTab(QWidget):
    """
    Kullanıcı tercihlerini (kısayol, popup süresi, oto-kopyalama/okuma)
    yöneten ve kaydeden ayarlar sekmesi bileşeni.
    """
    settings_saved = Signal()

    def __init__(self, settings_service: SettingsService):
        super().__init__()
        self.settings_service = settings_service
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        self.setStyleSheet("""
            QWidget {
                color: #FFFFFF;
                font-family: 'Segoe UI', sans-serif;
            }
            QGroupBox {
                border: 1px solid #333333;
                border-radius: 8px;
                margin-top: 10px;
                color: #0078D4;
                font-weight: bold;
                font-size: 13px;
            }
            QCheckBox {
                font-size: 13px;
                spacing: 8px;
            }
            QComboBox {
                background-color: #252526;
                color: #FFFFFF;
                border: 1px solid #3E3E42;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton {
                background-color: #0078D4;
                color: white;
                font-size: 13px;
                font-weight: bold;
                border-radius: 6px;
                padding: 10px 20px;
                border: none;
            }
            QPushButton:hover {
                background-color: #106EBE;
            }
        """)

        # 1. Otomatik Davranış Ayarları
        behavior_group = QGroupBox("Otomatik Davranışlar")
        b_layout = QVBoxLayout(behavior_group)
        b_layout.setSpacing(10)

        self.chk_auto_copy = QCheckBox("📋 Çeviri yapıldığında sonucu otomatik panoya kopyala")
        b_layout.addWidget(self.chk_auto_copy)

        self.chk_auto_tts = QCheckBox("🔊 Çeviri yapıldığında sonucu otomatik sesli oku (TTS)")
        b_layout.addWidget(self.chk_auto_tts)

        layout.addWidget(behavior_group)

        # 2. Popup & Zamanlama Ayarları
        popup_group = QGroupBox("Popup & Kısayol Yapılandırması")
        p_layout = QVBoxLayout(popup_group)
        p_layout.setSpacing(12)

        # Popup Süresi
        duration_layout = QHBoxLayout()
        lbl_dur = QLabel("Popup Ekranda Kalma Süresi:")
        lbl_dur.setStyleSheet("font-size: 13px;")
        duration_layout.addWidget(lbl_dur)

        self.cmb_duration = QComboBox()
        self.cmb_duration.addItem("Tıklayana Kadar Kapanmasın (Varsayılan)", 0)
        self.cmb_duration.addItem("3 Saniye", 3)
        self.cmb_duration.addItem("5 Saniye", 5)
        self.cmb_duration.addItem("10 Saniye", 10)
        duration_layout.addWidget(self.cmb_duration)
        p_layout.addLayout(duration_layout)

        # Kısayol Seçimi
        hotkey_layout = QHBoxLayout()
        lbl_hk = QLabel("Varsayılan Global Kısayol:")
        lbl_hk.setStyleSheet("font-size: 13px;")
        hotkey_layout.addWidget(lbl_hk)

        self.cmb_hotkey = QComboBox()
        self.cmb_hotkey.addItem("Alt + S (Tavsiye Edilen)", "Alt+S")
        self.cmb_hotkey.addItem("F8 (Tek Tuş)", "F8")
        self.cmb_hotkey.addItem("Ctrl + Alt + S", "Ctrl+Alt+S")
        hotkey_layout.addWidget(self.cmb_hotkey)
        p_layout.addLayout(hotkey_layout)

        layout.addWidget(popup_group)

        # Kaydet Butonu
        save_btn = QPushButton("💾 Ayarları Kaydet")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)

        layout.addStretch()

    def load_settings(self):
        auto_copy = self.settings_service.get("auto_copy", True)
        auto_tts = self.settings_service.get("auto_tts", False)
        duration = self.settings_service.get("popup_duration", 5)
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
        msg.setStyleSheet("background-color: #252526; color: #FFFFFF;")
        msg.exec()
