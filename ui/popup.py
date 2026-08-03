from PySide6.QtCore import Qt, QTimer, QRect
from PySide6.QtGui import QFont, QColor, QGuiApplication
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGraphicsDropShadowEffect, QMessageBox
)


class TranslationPopup(QWidget):
    """
    PySide6 ile oluşturulmuş modern çeviri popup penceresi (Aşama 4):
    - Koyu yarı saydam arka plan (#1E1E1EEE / rgba(30, 30, 30, 0.93))
    - Beyaz yazı & 12px border radius
    - Hafif drop shadow gölge efekti
    - Maksimum genişlik 420px
    - Metin fare ile seçilebilir (TextSelectableByMouse)
    - Seçim dikdörtgeninin sağ altına yakın konumlama
    - Ekran dışına taşarsa otomatik konum düzeltmesi
    - 5 saniye sonra otomatik kaybolma
    """
    def __init__(self, original_text: str, translated_text: str, source_lang: str, target_lang: str, rect: QRect):
        super().__init__()
        # Çerçevesiz, en üstte, görev çubuğunda simge oluşturmayan pencere
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.setMaximumWidth(420)
        self.setup_ui(original_text, translated_text, source_lang, target_lang)
        self.apply_shadow_effect()
        self.position_near_bottom_right(rect)

        # 5 saniye (5000 ms) sonra otomatik kaybolma zamanlayıcısı
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.close)
        self.timer.start(5000)

    def setup_ui(self, original_text: str, translated_text: str, source_lang: str, target_lang: str):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Koyu yarı saydam kart (#1E1E1EEE -> rgba(30, 30, 30, 0.93), 12px border-radius)
        container = QWidget()
        container.setObjectName("popupContainer")
        container.setStyleSheet("""
            QWidget#popupContainer {
                background-color: rgba(30, 30, 30, 0.93);
                border: 1.5px solid #0078D4;
                border-radius: 12px;
            }
            QLabel {
                color: #FFFFFF;
                font-family: 'Segoe UI', sans-serif;
            }
        """)

        card_layout = QVBoxLayout(container)
        card_layout.setSpacing(8)
        card_layout.setContentsMargins(16, 14, 16, 14)

        # Üst Dil Rozeti (örn: 🌐 EN ➜ TR)
        header_layout = QHBoxLayout()
        lang_badge = QLabel(f"🌐  {source_lang.upper()}  ➜  {target_lang.upper()}")
        lang_badge.setStyleSheet("color: #00E5FF; font-weight: bold; font-size: 11px;")
        header_layout.addWidget(lang_badge)
        header_layout.addStretch()
        card_layout.addLayout(header_layout)

        # Çeviri Metni (Fare ile Seçilebilir)
        trans_label = QLabel(translated_text)
        trans_label.setWordWrap(True)
        trans_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        trans_label.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: 600; line-height: 1.4;")
        card_layout.addWidget(trans_label)

        # Orijinal Metin (Seçilebilir ve İpucu şeklinde)
        if original_text and len(original_text) < 150:
            orig_label = QLabel(f"“{original_text}”")
            orig_label.setWordWrap(True)
            orig_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            orig_label.setStyleSheet("color: #A0A0A0; font-size: 11px; font-style: italic;")
            card_layout.addWidget(orig_label)

        main_layout.addWidget(container)
        self.adjustSize()

    def apply_shadow_effect(self):
        """Hafif drop shadow gölge efekti ekler."""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(18)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

    def position_near_bottom_right(self, rect: QRect):
        """
        Popup penceresini seçilen alanın sağ altına yakın konumlandırır.
        Ekran sınırlarını aşarsa otomatik konum düzeltmesi yapar.
        """
        screen = QGuiApplication.screenAt(rect.center()) or QGuiApplication.primaryScreen()
        screen_geo = screen.geometry()

        popup_w = min(420, max(260, self.width()))
        popup_h = self.height()

        # Varsayılan Hedef Konum: Seçilen alanın sağ alt yakını
        pos_x = rect.right() - 20
        pos_y = rect.bottom() + 10

        # Ekranın sağ kenarından taşıyorsa sola kaydır
        if pos_x + popup_w > screen_geo.right() - 12:
            pos_x = screen_geo.right() - popup_w - 12
        # Ekranın sol kenarından taşıyorsa sağa kaydır
        if pos_x < screen_geo.left() + 12:
            pos_x = screen_geo.left() + 12

        # Ekranın alt kenarından taşıyorsa yukarı (seçimin üstüne) taşı
        if pos_y + popup_h > screen_geo.bottom() - 12:
            pos_y = max(screen_geo.top() + 12, rect.top() - popup_h - 10)

        self.setGeometry(pos_x, pos_y, popup_w, popup_h)


def show_error_popup(parent: QWidget, title: str, message: str):
    """Hata veya uyarı mesaj kutusu."""
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Warning)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)

    msg_box.setStyleSheet("""
        QMessageBox {
            background-color: #252526;
            color: #FFFFFF;
            font-family: 'Segoe UI', sans-serif;
            font-size: 13px;
        }
        QLabel {
            color: #FFFFFF;
            font-size: 13px;
        }
        QPushButton {
            background-color: #0078D4;
            color: white;
            padding: 6px 20px;
            border-radius: 4px;
            font-weight: bold;
            min-width: 70px;
        }
        QPushButton:hover {
            background-color: #106EBE;
        }
    """)
    msg_box.exec()
