import sys
import ctypes
from ctypes import wintypes
from PySide6.QtCore import Qt, QRect, QPoint, Signal
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QGuiApplication
from PySide6.QtWidgets import QWidget


class SelectionOverlay(QWidget):
    """
    Ekranı karartmayan, tamamen şeffaf olan, yalnızca ince mavi çerçeve gösteren
    ve Windows DPI ölçeklendirmesini (%125, %150 vb.) doğru hesaplayan seçim bileşeni.
    """
    # Seçim bittiğinde tetiklenen sinyal: (logical_rect, physical_coords_tuple)
    area_selected = Signal(QRect, tuple)
    cancelled = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setCursor(Qt.CursorShape.ArrowCursor)

        self.start_point = None
        self.end_point = None
        self.is_selecting = False

    def start_selection(self):
        """Seçim modunu başlatır ve tüm ekranları kaplar."""
        virtual_rect = QRect()
        for screen in QGuiApplication.screens():
            virtual_rect = virtual_rect.united(screen.geometry())

        self.setGeometry(virtual_rect)
        self.start_point = None
        self.end_point = None
        self.is_selecting = False
        self.show()
        self.activateWindow()
        self.raise_()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_point = event.globalPosition().toPoint()
            self.end_point = self.start_point
            self.is_selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self.is_selecting:
            self.end_point = event.globalPosition().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_selecting:
            self.end_point = event.globalPosition().toPoint()
            self.is_selecting = False
            self.hide()

            selection_rect = QRect(self.start_point, self.end_point).normalized()

            if selection_rect.width() > 5 and selection_rect.height() > 5:
                # Windows DPI Scaling (%125, %150 vb.) hesaplaması
                screen = QGuiApplication.screenAt(self.start_point) or QGuiApplication.primaryScreen()
                scale_factor = screen.devicePixelRatio()

                # Fiziksel ekran piksel koordinatlarına dönüştürme (DPI duyarlı)
                phys_x = int(selection_rect.x() * scale_factor)
                phys_y = int(selection_rect.y() * scale_factor)
                phys_w = int(selection_rect.width() * scale_factor)
                phys_h = int(selection_rect.height() * scale_factor)

                physical_coords = (phys_x, phys_y, phys_w, phys_h)
                self.area_selected.emit(selection_rect, physical_coords)
            else:
                self.cancelled.emit()

    def keyPressEvent(self, event):
        # ESC tuşuna basıldığında seçimi iptal et
        if event.key() == Qt.Key.Key_Escape:
            self.is_selecting = False
            self.hide()
            self.cancelled.emit()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Buffer Temizliği (Windows Translucent Pencere İz Bırakma / Çizgi Birikmesi Çözümü)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

        # Fare olaylarını yakalamak için 1/255 transparan dolgu
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))

        if self.start_point and self.end_point and self.is_selecting:
            global_rect = QRect(self.start_point, self.end_point).normalized()
            local_top_left = self.mapFromGlobal(global_rect.topLeft())
            local_bottom_right = self.mapFromGlobal(global_rect.bottomRight())
            local_rect = QRect(local_top_left, local_bottom_right)

            full_region = self.rect()
            
            # Kurumsal Mat Dış Karartma Maskesi (Gözü yormayan %45 mat koyu zemin)
            painter.save()
            overlay_color = QColor(15, 15, 20, 115)
            
            # Üst
            painter.fillRect(QRect(0, 0, full_region.width(), local_rect.top()), overlay_color)
            # Alt
            painter.fillRect(QRect(0, local_rect.bottom() + 1, full_region.width(), full_region.height() - local_rect.bottom()), overlay_color)
            # Sol
            painter.fillRect(QRect(0, local_rect.top(), local_rect.left(), local_rect.height() + 1), overlay_color)
            # Sağ
            painter.fillRect(QRect(local_rect.right() + 1, local_rect.top(), full_region.width() - local_rect.right(), local_rect.height() + 1), overlay_color)
            painter.restore()

            # Jilet Gibi Keskin Kurumsal Mavi Çerçeve (#0078D4)
            border_pen = QPen(QColor(0, 120, 212), 1.5, Qt.PenStyle.SolidLine)
            painter.setPen(border_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(local_rect, 4, 4)

            # Minimalist Kurumsal Boyut Gösterge Etiketi (Dimension Badge: W x H px)
            w = local_rect.width()
            h = local_rect.height()
            if w > 35 and h > 15:
                badge_text = f"{w} × {h} px"
                font = painter.font()
                font.setPointSize(9)
                font.setWeight(QFont.Weight.Medium)
                font.setFamily("Segoe UI")
                painter.setFont(font)

                metrics = painter.fontMetrics()
                bw = metrics.horizontalAdvance(badge_text) + 14
                bh = 20

                # Etiketi kutunun hemen altına koy
                bx = local_rect.left()
                by = local_rect.bottom() + 6
                if by + bh > full_region.bottom() - 10:
                    by = local_rect.top() - bh - 6

                badge_rect = QRect(bx, by, bw, bh)
                painter.setPen(QPen(QColor(63, 63, 70), 1))
                painter.setBrush(QColor(24, 24, 27, 230))
                painter.drawRoundedRect(badge_rect, 3, 3)

                painter.setPen(QPen(QColor(212, 212, 216)))
                painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, badge_text)
