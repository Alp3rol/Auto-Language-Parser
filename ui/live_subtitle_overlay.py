import sys
from PySide6.QtCore import Qt, QPoint, Signal, QRect
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGraphicsDropShadowEffect
)


class LiveSubtitleOverlay(QWidget):
    """
    Canlı çeviri modunda ekranda üstte duran, yarı saydam, sürüklenebilir altyazı penceresi.
    """
    closed = Signal()
    paused_toggled = Signal(bool)

    def __init__(self, rect: QRect = None):
        super().__init__()
        self.is_paused = False

        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        if rect and rect.isValid():
            # Seçilen alanın hemen altına konumlandır
            self.setGeometry(rect.x(), rect.y() + rect.height() + 10, max(rect.width(), 360), 120)
        else:
            self.resize(480, 130)

        self.setup_ui()

    def setup_ui(self):
        container = QFrame(self)
        container.setObjectName("subtitleContainer")
        container.setStyleSheet("""
            QFrame#subtitleContainer {
                background-color: #18181B;
                border: 1px solid #3F3F46;
                border-radius: 12px;
            }
            QLabel {
                color: #FFFFFF;
                font-family: 'Segoe UI', -apple-system, sans-serif;
            }
        """)

        # Gölge efekti
        shadow = QGraphicsDropShadowEffect(container)
        shadow.setBlurRadius(16)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 4)
        container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(container)

        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(12, 8, 12, 12)
        c_layout.setSpacing(6)

        # Başlık Barı
        header_bar = QHBoxLayout()
        header_bar.setContentsMargins(0, 0, 0, 0)

        self.status_dot = QLabel("🔴")
        self.status_dot.setStyleSheet("font-size: 10px;")
        header_bar.addWidget(self.status_dot)

        self.title_label = QLabel("CANLI ALTYAZI ÇEVİRİSİ")
        self.title_label.setStyleSheet("font-size: 11px; font-weight: 800; color: #0078D4; letter-spacing: 0.8px;")
        header_bar.addWidget(self.title_label)

        header_bar.addStretch()

        # Duraklat / Devam Et Butonu
        self.pause_btn = QPushButton("⏸️")
        self.pause_btn.setToolTip("Canlı Taramayı Duraklat / Devam Ettir")
        self.pause_btn.setFixedSize(26, 24)
        self.pause_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
            }
        """)
        self.pause_btn.clicked.connect(self.toggle_pause)
        header_bar.addWidget(self.pause_btn)

        # Kapat Butonu
        close_btn = QPushButton("✕")
        close_btn.setToolTip("Canlı Modu Kapat")
        close_btn.setFixedSize(26, 24)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #A1A1AA;
                border: none;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #EF4444;
                color: #FFF;
                border-radius: 4px;
            }
        """)
        close_btn.clicked.connect(self.close)
        header_bar.addWidget(close_btn)

        c_layout.addLayout(header_bar)

        # Altyazı Metni Alanı
        self.subtitle_text = QLabel("Taranan alandaki canlı çeviri burada görüntülenecektir...")
        self.subtitle_text.setWordWrap(True)
        self.subtitle_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_text.setStyleSheet("""
            font-size: 14px;
            font-weight: 600;
            color: #00FF88;
            padding: 4px;
        """)
        c_layout.addWidget(self.subtitle_text, 1)

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.status_dot.setText("🟡")
            self.title_label.setText("CANLI ALTYAZI (DURAKLATILDI)")
            self.title_label.setStyleSheet("font-size: 11px; font-weight: 800; color: #FFCC00; letter-spacing: 0.8px;")
            self.pause_btn.setText("▶️")
        else:
            self.status_dot.setText("🔴")
            self.title_label.setText("CANLI ALTYAZI ÇEVİRİSİ")
            self.title_label.setStyleSheet("font-size: 11px; font-weight: 800; color: #0078D4; letter-spacing: 0.8px;")
            self.pause_btn.setText("⏸️")

        self.paused_toggled.emit(self.is_paused)

    def update_text(self, translated_text: str):
        """Çevrilen metni canlı olarak günceller."""
        if not translated_text or not translated_text.strip():
            return
        self.subtitle_text.setText(translated_text)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, '_drag_pos'):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)
