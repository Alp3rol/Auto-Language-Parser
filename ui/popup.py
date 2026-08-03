from PySide6.QtCore import Qt, QTimer, QRect, Signal
from PySide6.QtGui import QFont, QColor, QGuiApplication
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsDropShadowEffect, QMessageBox
)


class TranslationPopup(QWidget):
    """
    Ekran üzerinde seçilen metnin doğrudan ÜSTÜNE oturan (In-Place Overlay) çeviri kutusu.
    - Seçim kutusuyla (rect) birebir aynı boyut ve konum (Görsel 2'deki gibi Cyan çerçeve)
    - Orijinal metni tamamen kapatır, sadece çeviriyi metin alanında gösterir
    - Tıklanınca panoya kopyalar, sağ tıklanınca hızlı aksiyon menüsü açar
    """
    copy_requested = Signal(str)
    speak_requested = Signal(str, str)

    def __init__(self, original_text: str, translated_text: str, source_lang: str, target_lang: str, rect: QRect, duration_sec: int = 6):
        super().__init__()
        self.original_text = original_text
        self.translated_text = translated_text
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.rect_target = rect

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.setup_ui(translated_text)
        self.apply_shadow_effect()
        self.fit_to_selection_rect(rect)

        # Süre > 0 ise otomatik kaybolma zamanlayıcısı
        if duration_sec > 0:
            self.timer = QTimer(self)
            self.timer.setSingleShot(True)
            self.timer.timeout.connect(self.close)
            self.timer.start(duration_sec * 1000)

    def setup_ui(self, translated_text: str):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # OCR/Çeviriden gelen yapay alt satır (\n) kırılmalarını birleştirerek doğal akış sağla
        display_text = " ".join(translated_text.splitlines()) if translated_text else ""

        # Kurumsal Derin Koyu Kart (#1E1E22) + 1.5px Kurumsal Mavi Çerçeve (#0078D4)
        self.container = QWidget()
        self.container.setObjectName("overlayContainer")
        self.container.setStyleSheet("""
            QWidget#overlayContainer {
                background-color: #1E1E22;
                border: 1.5px solid #0078D4;
                border-radius: 6px;
            }
            QLabel {
                color: #FFFFFF;
                font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            }
        """)

        card_layout = QVBoxLayout(self.container)
        card_layout.setContentsMargins(12, 6, 12, 6)
        card_layout.setSpacing(0)

        # Sadece Çeviri Metni (Yüksek Okunurluklu 14px/15px Kurumsal Tipografi)
        self.trans_label = QLabel(display_text)
        self.trans_label.setWordWrap(True)
        self.trans_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.trans_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        
        from PySide6.QtWidgets import QSizePolicy
        self.trans_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        font_size = 14
        if self.rect_target.height() < 28:
            font_size = 11
        elif self.rect_target.height() >= 45 or self.rect_target.width() > 350:
            font_size = 14.5

        self.trans_label.setStyleSheet(f"color: #FFFFFF; font-size: {font_size}px; font-weight: 600; line-height: 1.3;")
        card_layout.addWidget(self.trans_label)

        main_layout.addWidget(self.container)

    def apply_shadow_effect(self):
        """Derinlik katan yumuşak kurumsal gölge efekti."""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

    def fit_to_selection_rect(self, rect: QRect):
        """
        Popup'ı seçilen alanın (rect) üstüne 1:1 oturtur.
        Yapay kırılmalar temizlendiği için yazıyı büyük ve okunabilir 14px/15px fontta tutar.
        """
        screen = QGuiApplication.screenAt(rect.center()) or QGuiApplication.primaryScreen()
        screen_geo = screen.geometry()

        pos_x = rect.x()
        pos_y = rect.y()
        width = rect.width()
        target_h = rect.height()

        available_w = max(width - 24, 100)
        self.trans_label.setFixedWidth(available_w)
        self.adjustSize()

        hint_h = self.container.sizeHint().height()
        height = max(target_h, hint_h)

        # Ekran sınır kontrolü
        if pos_x + width > screen_geo.right() - 4:
            pos_x = max(screen_geo.left() + 4, screen_geo.right() - width - 4)
        if pos_x < screen_geo.left() + 4:
            pos_x = screen_geo.left() + 4

        if pos_y + height > screen_geo.bottom() - 4:
            pos_y = max(screen_geo.top() + 4, screen_geo.bottom() - height - 4)
        if pos_y < screen_geo.top() + 4:
            pos_y = screen_geo.top() + 4

        self.setGeometry(pos_x, pos_y, width, height)

    def mousePressEvent(self, event):
        """Üzerine tıklandığında (sol veya sağ tık) metni kopyalar ve popup'ı anında kapatır."""
        QGuiApplication.clipboard().setText(self.translated_text)
        self.copy_requested.emit(self.translated_text)
        self.close()
        super().mousePressEvent(event)


class LoadingPopup(QWidget):
    """Metin seçildiği 0. anda orijinal metnin üstünü kapatan kurumsal yükleme katmanı."""
    def __init__(self, rect: QRect):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        container = QWidget()
        container.setStyleSheet("""
            background-color: #1E1E22;
            border: 1.5px solid #0078D4;
            border-radius: 6px;
        """)

        layout = QHBoxLayout(container)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        label = QLabel("⏳ Okunuyor ve çevriliyor...")
        label.setStyleSheet("color: #E4E4E7; font-family: 'Segoe UI', sans-serif; font-size: 12px; font-weight: 600;")
        layout.addWidget(label)

        main_layout.addWidget(container)

        self.adjustSize()
        hint_w = self.sizeHint().width()
        hint_h = self.sizeHint().height()

        pos_x = rect.x()
        pos_y = rect.y()
        width = max(rect.width(), hint_w)
        height = max(rect.height(), hint_h)

        self.setGeometry(pos_x, pos_y, width, height)


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
