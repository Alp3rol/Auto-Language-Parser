from PySide6.QtCore import QObject, Qt
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon


def create_app_icon() -> QIcon:
    """Programatik olarak şık bir uygulama simgesi çizer."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    painter.setBrush(QColor(0, 120, 212))
    painter.setPen(QColor(0, 90, 160))
    painter.drawEllipse(2, 2, 60, 60)

    painter.setPen(QColor(255, 255, 255))
    font = painter.font()
    font.setPointSize(26)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "T")
    painter.end()

    return QIcon(pixmap)


class TrayManager(QObject):
    """
    Sistem tepsisi (System Tray) simgesi, menüsü ve bildirim yönetim sınıfı.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.tray_icon = None

    def setup_tray(self, callbacks: dict):
        """
        callbacks: {
            'show': func,
            'crop': func,
            'selection': func,
            'live': func,
            'quit': func
        }
        """
        icon = create_app_icon()
        self.tray_icon = QSystemTrayIcon(icon, self.parent_window)
        self.tray_icon.setToolTip("A.L.P. (Auto Language Parser)")

        menu = QMenu()

        show_action = QAction("Pencereyi Göster", self.parent_window)
        show_action.triggered.connect(callbacks.get("show"))
        menu.addAction(show_action)

        select_action = QAction("Seçim Yap (Alt+S / F8)", self.parent_window)
        select_action.triggered.connect(callbacks.get("crop"))
        menu.addAction(select_action)

        sel_translate_action = QAction(
            "📋 Seçili Metni Çevir (Alt+C)", self.parent_window
        )
        sel_translate_action.triggered.connect(callbacks.get("selection"))
        menu.addAction(sel_translate_action)

        live_action = QAction("📺 Canlı Çeviri Modu", self.parent_window)
        live_action.triggered.connect(callbacks.get("live"))
        menu.addAction(live_action)

        menu.addSeparator()
        quit_action = QAction("Çıkış", self.parent_window)
        quit_action.triggered.connect(callbacks.get("quit"))
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason):
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            if hasattr(self.parent_window, "show_and_activate"):
                self.parent_window.show_and_activate()

    def show_message(
        self, title: str, message: str, icon=QSystemTrayIcon.MessageIcon.Information, timeout: int = 3000
    ):
        if self.tray_icon:
            self.tray_icon.showMessage(title, message, icon, timeout)
