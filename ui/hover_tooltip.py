import sys
from PySide6.QtCore import Qt, QPoint, QRect, QTimer
from PySide6.QtGui import QColor, QFont, QGuiApplication
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGraphicsDropShadowEffect
)


class HoverTooltip(QWidget):
    """
    Fare ile bir kelimenin üzerinde durulduğunda beliren şık, hafif mikro-sözlük penceresi (Hover Tooltip).
    """
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(0)

        container = QFrame(self)
        container.setObjectName("tooltipContainer")
        container.setStyleSheet("""
            QFrame#tooltipContainer {
                background: #18181B;
                border: 1px solid #3F3F46;
                border-radius: 8px;
            }
            QLabel {
                color: #F4F4F5;
                font-family: 'Segoe UI', -apple-system, sans-serif;
            }
        """)

        shadow = QGraphicsDropShadowEffect(container)
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 3)
        container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        # 1. Başlık Barı (Kelime & Okunuş & Gramer Türü)
        h_bar = QHBoxLayout()
        h_bar.setSpacing(6)

        self.lbl_word = QLabel("word")
        self.lbl_word.setStyleSheet("font-size: 13px; font-weight: 700; color: #FFFFFF;")
        h_bar.addWidget(self.lbl_word)

        self.lbl_phonetic = QLabel("/wɜːrd/")
        self.lbl_phonetic.setStyleSheet("font-size: 11px; color: #0078D4; font-weight: 500;")
        h_bar.addWidget(self.lbl_phonetic)

        self.lbl_pos = QLabel("noun")
        self.lbl_pos.setStyleSheet("font-size: 9px; background-color: #27272A; color: #A1A1AA; border-radius: 3px; padding: 1px 4px;")
        h_bar.addWidget(self.lbl_pos)

        h_bar.addStretch()
        layout.addLayout(h_bar)

        # 2. Türkçe Anlamı
        self.lbl_tr = QLabel("Kelime Türkçe Anlamı")
        self.lbl_tr.setWordWrap(True)
        self.lbl_tr.setStyleSheet("font-size: 12px; font-weight: 600; color: #00FF88;")
        layout.addWidget(self.lbl_tr)

        # 3. Örnek Cümle (Varsa)
        self.lbl_example = QLabel("")
        self.lbl_example.setWordWrap(True)
        self.lbl_example.setStyleSheet("font-size: 11px; color: #A1A1AA; font-style: italic;")
        layout.addWidget(self.lbl_example)

        main_layout.addWidget(container)

    def display_word(self, data: dict, pos_point: QPoint):
        """
        Sözlük verilerini doldurur ve imlecin hemen yanına konumlandırır.
        """
        if not data:
            self.hide()
            return

        self.lbl_word.setText(data.get("word", "").capitalize())
        self.lbl_phonetic.setText(data.get("phonetic", ""))
        self.lbl_pos.setText(data.get("pos", "word"))
        self.lbl_tr.setText(f"➔ {data.get('tr', '')}")

        ex = data.get("example", "")
        if ex:
            self.lbl_example.setText(f"“{ex}”")
            self.lbl_example.show()
        else:
            self.lbl_example.hide()

        self.adjustSize()
        width = self.sizeHint().width()
        height = self.sizeHint().height()

        screen = QGuiApplication.screenAt(pos_point) or QGuiApplication.primaryScreen()
        screen_geo = screen.geometry()

        pos_x = min(screen_geo.right() - width - 10, pos_point.x() + 14)
        pos_y = min(screen_geo.bottom() - height - 10, pos_point.y() + 18)

        self.setGeometry(pos_x, pos_y, width, height)
        self.show()
