import sys
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QColor, QFont, QGuiApplication, QPainter, QBrush, QPen
from PySide6.QtWidgets import QWidget


class InPlaceOverlay(QWidget):
    """
    Ekrandaki orijinal metni temizleyip (Inpainting/Background Sampling),
    çevirisini tam orijinal yazının konumunda grafiksel olarak doğrudan baştan çizen overlay.
    """
    def __init__(self, rect: QRect, translated_text: str, bg_color: QColor = None, text_color: QColor = None):
        super().__init__()
        self.rect_target = rect
        self.translated_text = " ".join(translated_text.splitlines()) if translated_text else ""
        self.bg_color = bg_color or QColor(24, 24, 27)
        self.text_color = text_color or QColor(255, 255, 255)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.setGeometry(rect)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. Orijinal yazının üzerini temizlemek için arka plan rengi çiz
        painter.setBrush(QBrush(self.bg_color))
        painter.setPen(QPen(QColor(0, 120, 212, 180), 1))
        painter.drawRoundedRect(self.rect(), 4, 4)

        # 2. Çevri metnini orijinal alanın tam ortasına yerleştir
        painter.setPen(QPen(self.text_color))
        font = QFont("Segoe UI", 12)
        font.setBold(True)
        painter.setFont(font)

        painter.drawText(
            self.rect().adjusted(6, 2, -6, -2),
            Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
            self.translated_text
        )

    def mousePressEvent(self, event):
        QGuiApplication.clipboard().setText(self.translated_text)
        self.close()
