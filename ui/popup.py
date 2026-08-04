from PySide6.QtCore import Qt, QTimer, QRect, Signal, QEvent
from PySide6.QtGui import QFont, QColor, QGuiApplication
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsDropShadowEffect, QMessageBox, QFrame
)


class TranslationPopup(QWidget):
    """
    A.L.P. Premium Obsidian Dark Çeviri Popup Penceresi.
    - Sade, mat koyu zemin (#18181B) ve ince şık gri çerçeve (#3F3F46)
    - Göze hitap eden sade dil rozeti (EN ➔ TR) ve aksiyon butonları
    - Yumuşak koyu gölge efekti ve yüksek okunabilirlikte tipografi
    """
    copy_requested = Signal(str)
    speak_requested = Signal(str, str)

    def __init__(self, original_text: str, translated_text: str, source_lang: str, target_lang: str, rect: QRect, duration_sec: int = 6, is_text_selection: bool = False):
        super().__init__()
        self.original_text = original_text
        self.translated_text = translated_text
        self.source_lang = source_lang or "en"
        self.target_lang = target_lang or "tr"
        self.rect_target = rect
        self.is_text_selection = is_text_selection

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.setup_ui(translated_text)
        self.apply_shadow_effect()
        self.fit_to_selection_rect(rect)

        if duration_sec > 0:
            self.timer = QTimer(self)
            self.timer.setSingleShot(True)
            self.timer.timeout.connect(self.close)
            self.timer.start(duration_sec * 1000)

    def setup_ui(self, translated_text: str):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(0)

        display_text = " ".join(translated_text.splitlines()) if translated_text else ""

        # Modern Mat Koyu Kart (Obsidian Theme)
        self.container = QFrame(self)
        self.container.setObjectName("popupContainer")
        self.container.setStyleSheet("""
            QFrame#popupContainer {
                background-color: #18181B;
                border: 1px solid #3F3F46;
                border-radius: 10px;
            }
            QLabel {
                color: #F4F4F5;
                font-family: 'Segoe UI', -apple-system, sans-serif;
            }
        """)

        card_layout = QVBoxLayout(self.container)
        card_layout.setContentsMargins(12, 8, 12, 8)
        card_layout.setSpacing(6)

        # 1. Başlık Barı (Header)
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(6)

        # Sade Dil Rozeti (Badge)
        src = self.source_lang.upper()
        tgt = self.target_lang.upper()
        badge_text = f"🌐 {src} ➔ {tgt}"
        self.badge = QLabel(badge_text)
        self.badge.setStyleSheet("""
            background-color: #27272A;
            color: #0078D4;
            font-size: 10px;
            font-weight: 700;
            border-radius: 4px;
            padding: 2px 7px;
            letter-spacing: 0.5px;
        """)
        header.addWidget(self.badge)

        header.addStretch()

        # Sesli Okuma Butonu
        btn_speak = QPushButton("🔊")
        btn_speak.setToolTip("Sesli Oku")
        btn_speak.setFixedSize(22, 22)
        btn_speak.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_speak.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 11px;
                color: #A1A1AA;
            }
            QPushButton:hover {
                background-color: #27272A;
                color: #FFFFFF;
                border-radius: 4px;
            }
        """)
        btn_speak.clicked.connect(lambda: self.speak_requested.emit(self.translated_text, self.target_lang))
        header.addWidget(btn_speak)

        # Kopyalama Butonu
        btn_copy = QPushButton("📋")
        btn_copy.setToolTip("Panoya Kopyala ve Kapat")
        btn_copy.setFixedSize(22, 22)
        btn_copy.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_copy.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 11px;
                color: #A1A1AA;
            }
            QPushButton:hover {
                background-color: #27272A;
                color: #00FF88;
                border-radius: 4px;
            }
        """)
        btn_copy.clicked.connect(self.copy_and_close)
        header.addWidget(btn_copy)

        # Kapat Butonu
        btn_close = QPushButton("✕")
        btn_close.setToolTip("Kapat")
        btn_close.setFixedSize(22, 22)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #A1A1AA;
                border: none;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #EF4444;
                color: #FFFFFF;
                border-radius: 4px;
            }
        """)
        btn_close.clicked.connect(self.close)
        header.addWidget(btn_close)

        card_layout.addLayout(header)

        # 2. Çeviri Metni Alanı
        self.trans_label = QLabel(display_text)
        self.trans_label.setWordWrap(True)
        self.trans_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        
        font_size = 13.5
        if self.rect_target.height() < 28 and not self.is_text_selection:
            font_size = 12

        self.trans_label.setStyleSheet(f"color: #F4F4F5; font-size: {font_size}px; font-weight: 600; line-height: 1.4;")
        card_layout.addWidget(self.trans_label)

        main_layout.addWidget(self.container)

        self.container.installEventFilter(self)
        self.trans_label.installEventFilter(self)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                btn_class_name = watched.metaObject().className()
                if btn_class_name != "QPushButton":
                    self.copy_and_close()
                    return True
        return super().eventFilter(watched, event)

    def apply_shadow_effect(self):
        """Derinlik katan sade koyu gölge efekti."""
        shadow = QGraphicsDropShadowEffect(self.container)
        shadow.setBlurRadius(16)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 4)
        self.container.setGraphicsEffect(shadow)

    def fit_to_selection_rect(self, rect: QRect):
        """
        Popup'ı seçilen alanın (rect) doğrudan üstüne ve görünür alana oturtur.
        """
        screen = QGuiApplication.screenAt(rect.center()) or QGuiApplication.primaryScreen()
        screen_geo = screen.geometry()

        text_len = len(self.translated_text)

        if self.is_text_selection or rect.width() < 220:
            calculated_w = min(480, max(320, text_len * 6))
            self.trans_label.setFixedWidth(calculated_w - 28)
            self.adjustSize()
            hint = self.container.sizeHint()
            width = calculated_w
            height = hint.height() + 20

            # Fare imlecinin hemen 15px altında kompakt ve temiz şekilde aç
            pos_x = rect.x() - (width // 4)
            pos_y = rect.y() + 15
        else:
            width = max(rect.width() + 24, 260)
            target_h = rect.height()

            available_w = max(width - 32, 200)
            self.trans_label.setFixedWidth(available_w)
            self.adjustSize()

            hint_h = self.container.sizeHint().height()
            height = max(target_h + 20, hint_h + 20)

            pos_x = rect.x() - 10
            pos_y = rect.y() - 10

        # Ekran sınır kontrolleri
        if pos_x + width > screen_geo.right() - 8:
            pos_x = screen_geo.right() - width - 8
        if pos_x < screen_geo.left() + 8:
            pos_x = screen_geo.left() + 8

        if pos_y + height > screen_geo.bottom() - 8:
            pos_y = screen_geo.bottom() - height - 8
        if pos_y < screen_geo.top() + 8:
            pos_y = screen_geo.top() + 8

        self.setGeometry(pos_x, pos_y, width, height)

    def copy_and_close(self):
        try:
            cb = QGuiApplication.clipboard()
            cb.blockSignals(True)
            cb.setText(self.translated_text)
            cb.blockSignals(False)
        except Exception:
            pass
        self.copy_requested.emit(self.translated_text)
        self.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.copy_and_close()
        super().mousePressEvent(event)


class LoadingPopup(QWidget):
    """
    Ekran veya metin seçildiğinde beliren sade, mat koyu yükleme katmanı (Compact Floating Pill).
    """
    def __init__(self, rect: QRect):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(0)

        container = QFrame()
        container.setObjectName("loadContainer")
        container.setStyleSheet("""
            QFrame#loadContainer {
                background: #18181B;
                border: 1px solid #3F3F46;
                border-radius: 14px;
            }
            QLabel {
                color: #F4F4F5;
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
                font-weight: 600;
            }
        """)

        shadow = QGraphicsDropShadowEffect(container)
        shadow.setBlurRadius(14)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 3)
        container.setGraphicsEffect(shadow)

        layout = QHBoxLayout(container)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel("⚡ Metin okunuyor ve çevriliyor...")
        layout.addWidget(label)

        main_layout.addWidget(container)

        self.adjustSize()
        hint_w = self.sizeHint().width()
        hint_h = self.sizeHint().height()

        screen = QGuiApplication.screenAt(rect.center()) or QGuiApplication.primaryScreen()
        screen_geo = screen.geometry()

        pos_x = max(screen_geo.left() + 10, rect.x() + (rect.width() - hint_w) // 2)
        pos_y = max(screen_geo.top() + 10, rect.y() - hint_h - 6)

        if pos_y < screen_geo.top() + 10:
            pos_y = rect.y() + 10

        self.setGeometry(pos_x, pos_y, hint_w + 16, hint_h + 16)


def show_error_popup(parent: QWidget, title: str, message: str):
    """Hata veya uyarı mesaj kutusu."""
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Warning)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)

    msg_box.setStyleSheet("""
        QMessageBox {
            background-color: #18181B;
            color: #FFFFFF;
            font-family: 'Segoe UI', sans-serif;
            font-size: 13px;
        }
        QLabel {
            color: #FFFFFF;
            font-size: 13px;
        }
        QPushButton {
            background-color: #0078D4;
            color: white;
            padding: 6px 20px;
            border-radius: 6px;
            font-weight: bold;
            min-width: 70px;
            border: none;
        }
        QPushButton:hover {
            background-color: #106EBE;
        }
    """)
    msg_box.exec()
