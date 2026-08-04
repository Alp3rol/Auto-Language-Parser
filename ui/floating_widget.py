import sys
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QFrame, QGraphicsDropShadowEffect
)


class FloatingWidget(QWidget):
    """
    Masaüstünde sürüklenebilen minimal, şeffaf hızlı erişim araç çubuğu (Floating Quick Toolbar).
    """
    capture_requested = Signal()
    selection_requested = Signal()
    live_requested = Signal()
    settings_requested = Signal()
    closed = Signal()

    def __init__(self, opacity: int = 90):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowOpacity(max(0.3, min(1.0, opacity / 100.0)))

        self.setup_ui()
        self.resize(270, 42)

    def setup_ui(self):
        container = QFrame(self)
        container.setObjectName("floatingContainer")
        container.setStyleSheet("""
            QFrame#floatingContainer {
                background-color: rgba(24, 24, 27, 0.95);
                border: 1px solid #3F3F46;
                border-radius: 20px;
            }
            QPushButton {
                background: transparent;
                color: #F4F4F5;
                border: none;
                font-size: 13px;
                font-weight: 600;
                padding: 4px 8px;
                border-radius: 12px;
            }
            QPushButton:hover {
                background-color: #0078D4;
                color: #FFFFFF;
            }
            QPushButton#btnSel:hover {
                background-color: #00FF88;
                color: #000000;
            }
            QPushButton#btnLive:hover {
                background-color: #00E5FF;
                color: #000000;
            }
            QPushButton#btnClose:hover {
                background-color: #EF4444;
                color: #FFFFFF;
            }
        """)

        # Hafif gölge efekti
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 140))
        shadow.setOffset(0, 4)
        container.setGraphicsEffect(shadow)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(container)

        c_layout = QHBoxLayout(container)
        c_layout.setContentsMargins(8, 4, 8, 4)
        c_layout.setSpacing(4)

        # Sürükleme kulpu (Drag handle)
        drag_handle = QLabel("⋮⋮")
        drag_handle.setToolTip("Sürüklemek için basılı tutun")
        drag_handle.setStyleSheet("color: #71717A; font-weight: bold; font-size: 12px; padding: 0 4px;")
        drag_handle.setCursor(Qt.CursorShape.SizeAllCursor)
        c_layout.addWidget(drag_handle)

        # 1. Tek Tık Ekran Çevirisi Butonu
        self.btn_capture = QPushButton("🎯")
        self.btn_capture.setToolTip("Ekran Çevirisi Yap (Alt+S)")
        self.btn_capture.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_capture.clicked.connect(self.capture_requested.emit)
        c_layout.addWidget(self.btn_capture)

        # 2. Seçili Metni Çevir Butonu
        self.btn_selection = QPushButton("📋")
        self.btn_selection.setObjectName("btnSel")
        self.btn_selection.setToolTip("Ekranda Seçili Metni Çevir (Alt+C)")
        self.btn_selection.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_selection.clicked.connect(self.selection_requested.emit)
        c_layout.addWidget(self.btn_selection)

        # 3. Canlı Altyazı Modu Butonu
        btn_live = QPushButton("📺")
        btn_live.setObjectName("btnLive")
        btn_live.setToolTip("Canlı Altyazı Çeviri Modu")
        btn_live.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_live.clicked.connect(self.live_requested.emit)
        c_layout.addWidget(btn_live)

        # 4. Ayarlar / Ana Pencere Butonu
        btn_settings = QPushButton("⚙️")
        btn_settings.setToolTip("A.L.P. Ana Penceresini Aç")
        btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_settings.clicked.connect(self.settings_requested.emit)
        c_layout.addWidget(btn_settings)

        # 5. Kapat Butonu
        btn_close = QPushButton("✕")
        btn_close.setObjectName("btnClose")
        btn_close.setToolTip("Yüzen Barı Gizle")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.hide_widget)
        c_layout.addWidget(btn_close)

    def update_tooltips(self, crop_preset: str = "Alt+S", sel_preset: str = "Alt+C"):
        """Dinamik kısayol ayarlarını buton ipuçlarına (tooltip) yansıtır."""
        if hasattr(self, 'btn_capture'):
            self.btn_capture.setToolTip(f"Ekran Çevirisi Yap ({crop_preset})")
        if hasattr(self, 'btn_selection'):
            self.btn_selection.setToolTip(f"Ekranda Seçili Metni Çevir ({sel_preset})")

    def set_opacity_percent(self, opacity: int):
        self.setWindowOpacity(max(0.3, min(1.0, opacity / 100.0)))

    def hide_widget(self):
        self.hide()
        self.closed.emit()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, '_drag_pos'):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
