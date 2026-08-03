from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QApplication
)
from services.history_service import HistoryService
from services.tts_service import TTSService


class HistoryTab(QWidget):
    """
    Çeviri geçmişini listeleyen, arama yaptıran, sesli okutan ve panoya kopyalayan sekme bileşeni.
    """
    def __init__(self, history_service: HistoryService, tts_service: TTSService):
        super().__init__()
        self.history_service = history_service
        self.tts_service = tts_service

        self.setup_ui()
        self.load_history()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Üst Araç Çubuğu (Arama Çubuğu + Temizle Butonu)
        top_bar = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Geçmişte ara...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #09090B;
                color: #F4F4F5;
                border: 1px solid #27272A;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #0078D4;
            }
        """)
        self.search_input.textChanged.connect(self.filter_history)
        top_bar.addWidget(self.search_input)

        clear_btn = QPushButton("🗑️ Temizle")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #27272A;
                color: #EF4444;
                border: 1px solid #3F3F46;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #EF4444;
                color: #FFFFFF;
            }
        """)
        clear_btn.clicked.connect(self.clear_history)
        top_bar.addWidget(clear_btn)

        layout.addLayout(top_bar)

        # Geçmiş Tablosu
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Zaman", "Dil", "Orijinal Metin", "Çeviri", "İşlem"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #09090B;
                color: #F4F4F5;
                gridline-color: #27272A;
                border: 1px solid #27272A;
                border-radius: 6px;
            }
            QHeaderView::section {
                background-color: #18181B;
                color: #A1A1AA;
                padding: 6px;
                font-weight: 600;
                font-size: 11px;
                border: none;
                border-bottom: 1px solid #27272A;
            }
            QTableWidget::item:selected {
                background-color: #27272A;
                color: #F4F4F5;
            }
        """)
        layout.addWidget(self.table)

    def load_history(self):
        items = self.history_service.get_history()
        self.populate_table(items)

    def populate_table(self, items: list):
        self.table.setRowCount(0)
        for row_idx, item in enumerate(items):
            self.table.insertRow(row_idx)

            time_item = QTableWidgetItem(item.get("timestamp", ""))
            lang_item = QTableWidgetItem(f"{item.get('source_lang', '')} ➔ {item.get('target_lang', '')}")
            orig_item = QTableWidgetItem(item.get("original_text", ""))
            trans_item = QTableWidgetItem(item.get("translated_text", ""))

            time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            lang_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.table.setItem(row_idx, 0, time_item)
            self.table.setItem(row_idx, 1, lang_item)
            self.table.setItem(row_idx, 2, orig_item)
            self.table.setItem(row_idx, 3, trans_item)

            # İşlem Butonları (Dinle & Kopyala)
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 2, 2, 2)
            action_layout.setSpacing(4)

            listen_btn = QPushButton("🔊")
            listen_btn.setToolTip("Çeviriyi Dinle")
            listen_btn.setFixedWidth(28)
            listen_btn.setStyleSheet("padding: 2px; font-size: 11px;")
            listen_btn.clicked.connect(lambda _, t=item.get("translated_text"), l=item.get("target_lang", "tr"): self.tts_service.speak(t, l))

            copy_btn = QPushButton("📋")
            copy_btn.setToolTip("Çeviriyi Kopyala")
            copy_btn.setFixedWidth(28)
            copy_btn.setStyleSheet("padding: 2px; font-size: 11px;")
            copy_btn.clicked.connect(lambda _, t=item.get("translated_text"): QApplication.clipboard().setText(t))

            action_layout.addWidget(listen_btn)
            action_layout.addWidget(copy_btn)
            self.table.setCellWidget(row_idx, 4, action_widget)

    def filter_history(self, query: str):
        query = query.lower().strip()
        items = self.history_service.get_history()
        if not query:
            self.populate_table(items)
            return

        filtered = [
            item for item in items
            if query in item.get("original_text", "").lower()
            or query in item.get("translated_text", "").lower()
            or query in item.get("timestamp", "").lower()
        ]
        self.populate_table(filtered)

    def clear_history(self):
        self.history_service.clear_history()
        self.load_history()
