import sys
import ctypes
from ctypes import wintypes
from PySide6.QtCore import Qt, QRect, QPoint, Signal
from PySide6.QtGui import QPainter, QPen, QColor, QGuiApplication
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
        self.setCursor(Qt.CursorShape.CrossCursor)

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

        # Arka planı tamamen şeffaf tutmak için 1/255 dolgu (Windows fare olaylarını yakalar, görsel kararma yapmaz)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))

        if self.start_point and self.end_point:
            global_rect = QRect(self.start_point, self.end_point).normalized()

            local_top_left = self.mapFromGlobal(global_rect.topLeft())
            local_bottom_right = self.mapFromGlobal(global_rect.bottomRight())
            local_rect = QRect(local_top_left, local_bottom_right)

            # Yalnızca ince mavi çerçeve (saydam iç dolgu yok)
            pen = QPen(QColor(0, 120, 212), 1.5, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)  # Tamamen şeffaf iç alan
            painter.drawRect(local_rect)
