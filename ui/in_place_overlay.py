import sys
from PIL import Image
from PySide6.QtCore import Qt, QRect, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QGuiApplication, QPainter, QBrush, QPen
from PySide6.QtWidgets import QWidget
from services.image_analysis import extract_dominant_bg_color, get_contrast_text_color


class InPlaceOverlay(QWidget):
    """
    Ekrandaki başlık, kalın metin, paragraf ve satır konumlarını birebir koruyarak (Layout-Aware AR Overlay)
    metinlerin üzerini ekranın kendi arka plan rengiyle kapatıp Türkçe çevirilerini tam orijinal yerinde çizen katman.
    """
    details_requested = Signal(str, QRect)

    def __init__(self, rect: QRect, translated_text: str = "", pil_image: Image.Image = None, structured_blocks: list = None):
        super().__init__()
        self.rect_target = rect
        self.translated_text = translated_text or ""
        self.structured_blocks = structured_blocks or []
        
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

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        # 1. Eğer elimizde yapısal bloklar (Başlık, Paragraf vs.) varsa blok bazında çizim yap
        if self.structured_blocks:
            for b in self.structured_blocks:
                bx = b.get("x", 0)
                by = b.get("y", 0)
                bw = b.get("w", 50)
                bh = b.get("h", 20)
                text = b.get("translated_text") or b.get("text") or ""
                is_heading = b.get("is_heading", False)
                is_bold = b.get("is_bold", False)
                line_height = b.get("line_height", bh)

                if not text.strip():
                    continue

                # Kutu koordinatları ve dolguları
                block_rect = QRect(bx, by, bw, bh)
                pad_rect = block_rect.adjusted(-3, -2, 3, 2)

                # Bloğun üzerini ekranın arka plan rengiyle kapat
                painter.setBrush(QBrush(self.bg_color))
                border_color = QColor(59, 130, 246, 180) if is_heading else QColor(39, 39, 42, 160)
                painter.setPen(QPen(border_color, 1))
                painter.drawRoundedRect(pad_rect, 4, 4)

                # Font boyutunu ve hiyerarşisini ayarla
                font = QFont("Segoe UI")
                if is_heading:
                    font_size = max(13, int(line_height * 0.75))
                    font.setWeight(QFont.Weight.Bold)
                    font.setItalic(True)
                    text_pen = QColor(56, 189, 248) if self.text_color.red() > 200 else QColor(3, 105, 161)
                else:
                    font_size = max(9, int(line_height * 0.65))
                    if is_bold:
                        font.setWeight(QFont.Weight.Bold)
                    text_pen = self.text_color

                font.setPointSize(font_size)
                painter.setFont(font)
                painter.setPen(QPen(text_pen))

                # Metni bloğun içerisine hizala
                painter.drawText(
                    pad_rect.adjusted(4, 1, -4, -1),
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextWordWrap,
                    text
                )
            return

        # 2. Yedek Akış: Blok verisi yoksa genel kutu olarak çiz
        painter.setBrush(QBrush(self.bg_color))
        painter.setPen(QPen(QColor(59, 130, 246, 200), 1.5))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)

        painter.setPen(QPen(self.text_color))
        font = QFont("Segoe UI", 11, QFont.Weight.Bold)
        painter.setFont(font)

        padding_rect = self.rect().adjusted(8, 5, -8, -5)
        display_text = " ".join(self.translated_text.splitlines()) if self.translated_text else ""
        painter.drawText(
            padding_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextWordWrap,
            display_text
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            copy_text = self.translated_text
            if not copy_text and self.structured_blocks:
                copy_text = "\n".join(b.get("translated_text", b.get("text", "")) for b in self.structured_blocks)
            QGuiApplication.clipboard().setText(copy_text)
            self.close()
        elif event.button() == Qt.MouseButton.RightButton:
            copy_text = self.translated_text
            if not copy_text and self.structured_blocks:
                copy_text = "\n".join(b.get("translated_text", b.get("text", "")) for b in self.structured_blocks)
            self.details_requested.emit(copy_text, self.rect_target)
            self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        super().keyPressEvent(event)
