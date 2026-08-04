import math
from PySide6.QtCore import Qt, Signal, QPoint, QRect, QTimer
from PySide6.QtGui import QColor, QFont, QGuiApplication
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QFrame, QGraphicsDropShadowEffect
)


class RadialMenu(QWidget):
    """
    Ekran alanı veya metin seçimi tamamlandığında imlecin etrafında beliren
    futuristlik dairesel (radial) aksiyon menüsü.
    """
    action_selected = Signal(str)
    closed = Signal()

    ACTIONS = [
        ("🔊", "speak", "Sesli Oku"),
        ("📋", "copy", "Panoya Kopyala"),
        ("🧠", "ai_explain", "AI Bağlam Açıklaması"),
        ("🎴", "vocab", "Kelime Kartlarına Ekle"),
        ("📌", "pin", "Ekrana Sabitle")
    ]

    def __init__(self, parent=None, radius: int = 65):
        super().__init__(parent)
        self.radius = radius
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setup_ui()

    def setup_ui(self):
        size = self.radius * 2 + 70
        self.setFixedSize(size, size)

        cx = size // 2
        cy = size // 2

        # Merkez Kapat Butonu
        self.center_btn = QPushButton("✕", self)
        self.center_btn.setFixedSize(30, 30)
        self.center_btn.move(cx - 15, cy - 15)
        self.center_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.center_btn.setToolTip("Kapat")
        self.center_btn.setStyleSheet("""
            QPushButton {
                background-color: #18181B;
                color: #A1A1AA;
                border: 1px solid #3F3F46;
                border-radius: 15px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #EF4444;
                color: #FFFFFF;
                border-color: #EF4444;
            }
        """)
        self.center_btn.clicked.connect(self.close_menu)

        # Dairesel İkon Butonları
        n_items = len(self.ACTIONS)
        btn_size = 36

        for i, (icon_str, act_key, tooltip_str) in enumerate(self.ACTIONS):
            angle = (2 * math.pi * i / n_items) - (math.pi / 2)
            bx = int(cx + self.radius * math.cos(angle) - btn_size / 2)
            by = int(cy + self.radius * math.sin(angle) - btn_size / 2)

            btn = QPushButton(icon_str, self)
            btn.setToolTip(tooltip_str)
            btn.setFixedSize(btn_size, btn_size)
            btn.move(bx, by)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

            btn.setStyleSheet("""
                QPushButton {
                    background-color: #18181B;
                    color: #F4F4F5;
                    border: 1.5px solid #3F3F46;
                    border-radius: 18px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #0078D4;
                    color: #FFFFFF;
                    border-color: #38BDF8;
                }
            """)
            btn.clicked.connect(lambda _, k=act_key: self._on_btn_clicked(k))

            # Gölge efekti
            shadow = QGraphicsDropShadowEffect(btn)
            shadow.setBlurRadius(10)
            shadow.setColor(QColor(0, 0, 0, 160))
            shadow.setOffset(0, 2)
            btn.setGraphicsEffect(shadow)

    def show_at_position(self, pos: QPoint):
        """Menüyü belirtilen ekran koordinatında (pos merkezli) konumlandırır ve gösterir."""
        w = self.width()
        h = self.height()
        pos_x = pos.x() - (w // 2)
        pos_y = pos.y() - (h // 2)

        screen = QGuiApplication.screenAt(pos) or QGuiApplication.primaryScreen()
        screen_geo = screen.geometry()

        if pos_x + w > screen_geo.right() - 8:
            pos_x = screen_geo.right() - w - 8
        if pos_x < screen_geo.left() + 8:
            pos_x = screen_geo.left() + 8
        if pos_y + h > screen_geo.bottom() - 8:
            pos_y = screen_geo.bottom() - h - 8
        if pos_y < screen_geo.top() + 8:
            pos_y = screen_geo.top() + 8

        self.setGeometry(pos_x, pos_y, w, h)
        self.show()
        self.raise_()

    def _on_btn_clicked(self, act_key: str):
        self.action_selected.emit(act_key)
        self.close_menu()

    def close_menu(self):
        self.close()
        self.closed.emit()
