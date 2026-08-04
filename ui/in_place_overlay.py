import sys
from PIL import Image
from PySide6.QtCore import Qt, QRect, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QGuiApplication, QPainter, QBrush, QPen
from PySide6.QtWidgets import QWidget
from services.image_analysis import extract_dominant_bg_color, get_contrast_text_color


class InPlaceOverlay(QWidget):
    """
    Ekrandaki seçili alanın üzerine arka plan rengine %100 uyumlu (Background Sampling),
    kristal netliğinde ve tek parça şık çeviri katmanı.
    """
    details_requested = Signal(str, QRect)

    def __init__(self, rect: QRect, translated_text: str = "", pil_image: Image.Image = None):
        super().__init__()
        self.rect_target = rect
        self.translated_text = translated_text or ""
        
        # Arka plan ve zıt yazı rengi tespiti
        self.bg_color = extract_dominant_bg_color(pil_image)
        self.text_color = get_contrast_text_color(self.bg_color)
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Sol Tık: Kopyala ve Kapat | Sağ Tık: Detaylar & AI Aksiyonları")

        self.setGeometry(rect)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        # 1. Pürüzsüz arka plan katmanı
        painter.setBrush(QBrush(self.bg_color))
        border_pen = QPen(QColor(59, 130, 246, 180), 1.5)  # İnce şık vurgu çerçevesi
        painter.setPen(border_pen)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 8, 8)

        # 2. Kristal netliğinde okunaklı metin
        painter.setPen(QPen(self.text_color))
        font = QFont("Segoe UI", 11, QFont.Weight.DemiBold)
        painter.setFont(font)

        padding_rect = self.rect().adjusted(10, 8, -10, -8)
        painter.drawText(
            padding_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextWordWrap,
            self.translated_text
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            QGuiApplication.clipboard().setText(self.translated_text)
            self.close()
        elif event.button() == Qt.MouseButton.RightButton:
            self.details_requested.emit(self.translated_text, self.rect_target)
            self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        super().keyPressEvent(event)
