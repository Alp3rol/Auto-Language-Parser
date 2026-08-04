import sys
from PIL import Image
from PySide6.QtCore import Qt, QRect, Signal, QTimer, QPoint
from PySide6.QtGui import QColor, QFont, QFontMetrics, QGuiApplication, QPainter, QBrush, QPen
from PySide6.QtWidgets import QWidget, QLabel, QGraphicsDropShadowEffect
from services.image_analysis import extract_dominant_bg_color, get_contrast_text_color


class InPlaceOverlay(QWidget):
    """
    Ekrandaki orijinal metnin üzerini, ekranın kendi arka plan rengiyle kapatıp (Background Sampling),
    çevirisini tam orijinal yazının durduğu koordinatlara doğrudan baştan çizen Gerçek Yerinde Çeviri Katmanı.
    """
    details_requested = Signal(str, QRect)

    def __init__(self, rect: QRect, translated_text: str, pil_image: Image.Image = None):
        super().__init__()
        self.rect_target = rect
        self.translated_text = " ".join(translated_text.splitlines()) if translated_text else ""
        
        # Arka plan ve yazı rengi tespiti
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
        self.font_size = self._calculate_optimal_font_size()

    def _calculate_optimal_font_size(self) -> int:
        """Kutu boyutuna göre çevirinin tam sığacağı optimal puntoyu hesaplar."""
        if not self.translated_text:
            return 12

        box_w = self.width() - 16
        box_h = self.height() - 10

        if box_w <= 20 or box_h <= 10:
            return 11

        for size in range(16, 8, -1):
            font = QFont("Segoe UI", size, QFont.Weight.Bold)
            fm = QFontMetrics(font)
            bound_rect = fm.boundingRect(
                0, 0, box_w, 2000,
                Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap,
                self.translated_text
            )
            if bound_rect.height() <= box_h:
                return size

        return 9

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        # 1. Orijinal metnin üzerini ekranın kendi arka plan rengiyle kapat
        painter.setBrush(QBrush(self.bg_color))
        border_pen = QPen(QColor(59, 130, 246, 200), 1.5)  # Mavi ince çerçeve
        painter.setPen(border_pen)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)

        # 2. Türkçe çevriyi orijinal konuma estetik şekilde yerleştir
        painter.setPen(QPen(self.text_color))
        font = QFont("Segoe UI", self.font_size, QFont.Weight.Bold)
        painter.setFont(font)

        padding_rect = self.rect().adjusted(8, 5, -8, -5)
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
