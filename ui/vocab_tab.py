from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QLineEdit, QMessageBox, QFileDialog
)
from services.vocab_service import VocabService
from services.anki_export_service import AnkiExportService



class VocabTab(QWidget):
    """
    Kullanıcının ekran çevirilerinden toplanan kelimeleri SM-2 Aralıklı Tekrar algoritması ile
    hafıza kartlarına (Flashcards) dönüştüren interaktif öğrenme sekmesi.
    """
    def __init__(self, vocab_service: VocabService):
        super().__init__()
        self.vocab_service = vocab_service
        self.current_due_cards = []
        self.current_card_index = 0
        self.is_answer_revealed = False

        self.setup_ui()
        self.load_due_cards()
        self.load_vocab_table()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Obsidian Dark Tema Stili
        self.setStyleSheet("""
            QWidget {
                background-color: #09090B;
                color: #F4F4F5;
                font-family: 'Segoe UI', -apple-system, sans-serif;
            }
            QFrame#cardBox {
                background-color: #18181B;
                border: 1px solid #3F3F46;
                border-radius: 12px;
            }
            QTableWidget {
                background-color: #18181B;
                color: #F4F4F5;
                border: 1px solid #27272A;
                border-radius: 8px;
                gridline-color: #27272A;
            }
            QHeaderView::section {
                background-color: #09090B;
                color: #A1A1AA;
                font-weight: 700;
                font-size: 11px;
                padding: 6px;
                border: none;
            }
            QLineEdit {
                background-color: #18181B;
                color: #F4F4F5;
                border: 1px solid #27272A;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
            }
            QPushButton#btnReveal {
                background-color: #0078D4;
                color: #FFFFFF;
                font-weight: 700;
                font-size: 13px;
                border-radius: 6px;
                padding: 8px;
                border: none;
            }
            QPushButton#btnReveal:hover {
                background-color: #106EBE;
            }
            QPushButton#btnGradeHard {
                background-color: #3F1D1D;
                color: #FF6B6B;
                border: 1px solid #7F1D1D;
                font-weight: 700;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton#btnGradeGood {
                background-color: #3F391D;
                color: #FFCC00;
                border: 1px solid #7F731D;
                font-weight: 700;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton#btnGradeEasy {
                background-color: #1D3F2B;
                color: #00FF88;
                border: 1px solid #1D7F4E;
                font-weight: 700;
                border-radius: 6px;
                padding: 6px 12px;
            }
        """)

        # ====================================================
        # BÖLÜM 1: 🎓 İNTERAKTİF FLASHCARD QUIZ KARTI
        # ====================================================
        lbl_quiz_hdr = QLabel("🎓 GÜNLÜK KELİME PRATİĞİ (FLASHCARD)")
        lbl_quiz_hdr.setStyleSheet("font-size: 11px; font-weight: 800; color: #A1A1AA; letter-spacing: 0.5px;")
        main_layout.addWidget(lbl_quiz_hdr)

        self.quiz_card = QFrame()
        self.quiz_card.setObjectName("cardBox")
        qc_layout = QVBoxLayout(self.quiz_card)
        qc_layout.setContentsMargins(16, 14, 16, 14)
        qc_layout.setSpacing(10)

        # Kart Sayacı & Durumu
        self.lbl_card_status = QLabel("Tekrar Edilecek Kart: 0")
        self.lbl_card_status.setStyleSheet("font-size: 11px; color: #0078D4; font-weight: 700;")
        qc_layout.addWidget(self.lbl_card_status)

        # Ön Yüz (İngilizce Kelime)
        self.lbl_word_front = QLabel("Henüz tekrar edilecek kelime yok 🎉")
        self.lbl_word_front.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_word_front.setStyleSheet("font-size: 18px; font-weight: 800; color: #FFFFFF;")
        qc_layout.addWidget(self.lbl_word_front)

        # Arka Yüz (Türkçe Anlamı)
        self.lbl_word_back = QLabel("")
        self.lbl_word_back.setWordWrap(True)
        self.lbl_word_back.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_word_back.setStyleSheet("font-size: 14px; font-weight: 600; color: #00FF88;")
        self.lbl_word_back.hide()
        qc_layout.addWidget(self.lbl_word_back)

        # Cevabı Göster Butonu
        self.btn_reveal = QPushButton("🔍 Cevabı Göster")
        self.btn_reveal.setObjectName("btnReveal")
        self.btn_reveal.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reveal.clicked.connect(self.reveal_answer)
        qc_layout.addWidget(self.btn_reveal)

        # Derece Butonları (Zor / İyi / Kolay)
        self.grade_box = QWidget()
        gb_layout = QHBoxLayout(self.grade_box)
        gb_layout.setContentsMargins(0, 0, 0, 0)
        gb_layout.setSpacing(8)

        btn_hard = QPushButton("🔴 Zor (1 Gün)")
        btn_hard.setObjectName("btnGradeHard")
        btn_hard.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_hard.clicked.connect(lambda: self.grade_card(1))
        gb_layout.addWidget(btn_hard)

        btn_good = QPushButton("🟡 İyi (3 Gün)")
        btn_good.setObjectName("btnGradeGood")
        btn_good.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_good.clicked.connect(lambda: self.grade_card(3))
        gb_layout.addWidget(btn_good)

        btn_easy = QPushButton("🟢 Kolay (6+ Gün)")
        btn_easy.setObjectName("btnGradeEasy")
        btn_easy.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_easy.clicked.connect(lambda: self.grade_card(5))
        gb_layout.addWidget(btn_easy)

        self.grade_box.hide()
        qc_layout.addWidget(self.grade_box)

        main_layout.addWidget(self.quiz_card)

        # ====================================================
        # BÖLÜM 2: 📚 KELİME BANKASI TABLOSU
        # ====================================================
        h_table_hdr = QHBoxLayout()
        lbl_tbl_hdr = QLabel("📚 KELİME BANKASI & GEÇMİŞİ")
        lbl_tbl_hdr.setStyleSheet("font-size: 11px; font-weight: 800; color: #A1A1AA; letter-spacing: 0.5px;")
        h_table_hdr.addWidget(lbl_tbl_hdr)

        self.btn_export_anki = QPushButton("📥 Anki Dışa Aktar")
        self.btn_export_anki.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export_anki.setStyleSheet("""
            QPushButton {
                background-color: #27272A;
                color: #00E5FF;
                border: 1px solid #00E5FF;
                border-radius: 6px;
                padding: 4px 8px;
                font-weight: 700;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #00E5FF;
                color: #000000;
            }
        """)
        self.btn_export_anki.clicked.connect(self.export_to_anki)
        h_table_hdr.addWidget(self.btn_export_anki)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Kelime ara...")
        self.txt_search.setFixedWidth(140)
        self.txt_search.textChanged.connect(self.filter_table)
        h_table_hdr.addWidget(self.txt_search)

        main_layout.addLayout(h_table_hdr)


        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "İngilizce Kelime", "Türkçe Anlamı", "Tekrar"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        main_layout.addWidget(self.table, stretch=1)

    def load_due_cards(self):
        self.current_due_cards = self.vocab_service.get_due_cards(limit=20)
        self.current_card_index = 0
        self.is_answer_revealed = False
        self.show_current_card()

    def show_current_card(self):
        count = len(self.current_due_cards)
        if count == 0 or self.current_card_index >= count:
            self.lbl_card_status.setText("✅ Bugünü Tamamladınız!")
            self.lbl_word_front.setText("Harika! Tüm kelime kartlarını tekrar ettiniz 🎉")
            self.lbl_word_back.hide()
            self.btn_reveal.hide()
            self.grade_box.hide()
            return

        card = self.current_due_cards[self.current_card_index]
        self.lbl_card_status.setText(f"Kalan Kart: {count - self.current_card_index} / {count}")
        self.lbl_word_front.setText(card["word"])
        self.lbl_word_back.setText(f"➔ {card['translation']}")

        self.lbl_word_back.hide()
        self.btn_reveal.show()
        self.grade_box.hide()
        self.is_answer_revealed = False

    def reveal_answer(self):
        self.lbl_word_back.show()
        self.btn_reveal.hide()
        self.grade_box.show()
        self.is_answer_revealed = True

    def grade_card(self, quality: int):
        if self.current_card_index < len(self.current_due_cards):
            card = self.current_due_cards[self.current_card_index]
            self.vocab_service.review_card(card["id"], quality)
            self.current_card_index += 1
            self.show_current_card()
            self.load_vocab_table()

    def load_vocab_table(self):
        words = self.vocab_service.get_all_words()
        self.table.setRowCount(len(words))
        for row, item in enumerate(words):
            self.table.setItem(row, 0, QTableWidgetItem(str(item["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(item["word"]))
            self.table.setItem(row, 2, QTableWidgetItem(item["translation"]))
            self.table.setItem(row, 3, QTableWidgetItem(f"{item['repetition_count']} Kez"))

    def filter_table(self, text: str):
        search = text.lower().strip()
        for row in range(self.table.rowCount()):
            word_item = self.table.item(row, 1)
            trans_item = self.table.item(row, 2)
            match = search in (word_item.text().lower() if word_item else "") or \
                    search in (trans_item.text().lower() if trans_item else "")
            self.table.setRowHidden(row, not match)

    def export_to_anki(self):
        words = self.vocab_service.get_all_words()
        if not words:
            QMessageBox.information(
                self, "Kelime Yok", "Dışa aktarılacak herhangi bir kelime bulunamadı."
            )
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Anki Destesini Kaydet",
            "alp_anki_deck.txt",
            "Anki Deck Files (*.txt *.tsv)"
        )
        if filepath:
            success = AnkiExportService.export_to_tsv(words, filepath)
            if success:
                QMessageBox.information(
                    self,
                    "Dışa Aktarıldı",
                    f"Tüm kelimeler Anki formatında başarıyla aktarıldı!\n\nDosya: {filepath}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Hata",
                    "Anki destesi oluşturulurken bir hata oluştu."
                )

