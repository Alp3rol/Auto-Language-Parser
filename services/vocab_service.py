import os
import sqlite3
import time
from datetime import datetime, timedelta


class VocabService:
    """
    Kullanıcının günlük ekran ve metin çevirilerinden bilinmeyen kelimeleri toplayan,
    Spaced Repetition (SM-2 Aralıklı Tekrar) algoritması ile hafıza kartına dönüştüren veritabanı servisi.
    """
    def __init__(self, db_path: str = None):
        if db_path is None:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "vocab_bank.db")

        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vocab_bank (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT NOT NULL UNIQUE,
                    translation TEXT NOT NULL,
                    src_lang TEXT DEFAULT 'en',
                    tgt_lang TEXT DEFAULT 'tr',
                    ease_factor REAL DEFAULT 2.5,
                    interval_days INTEGER DEFAULT 1,
                    repetition_count INTEGER DEFAULT 0,
                    next_review_timestamp REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_vocab_next_review 
                ON vocab_bank(next_review_timestamp);
            """)
            conn.commit()

    def add_word(self, word: str, translation: str, src_lang: str = "en", tgt_lang: str = "tr") -> bool:
        clean_word = word.strip()
        clean_trans = translation.strip()

        if not clean_word or not clean_trans:
            return False

        # Tek bir kelime veya kısa kelime grubu değilse kaydetme
        if len(clean_word.split()) > 4:
            return False

        now_ts = time.time()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO vocab_bank (word, translation, src_lang, tgt_lang, next_review_timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, (clean_word, clean_trans, src_lang, tgt_lang, now_ts))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                # Zaten kayıtlıysa güncelle
                cursor.execute("""
                    UPDATE vocab_bank SET translation = ?, tgt_lang = ? WHERE word = ?
                """, (clean_trans, tgt_lang, clean_word))
                conn.commit()
                return True

    def get_due_cards(self, limit: int = 20) -> list[dict]:
        """Tekrar zamanı gelmiş kartları getirir."""
        now_ts = time.time()
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM vocab_bank
                WHERE next_review_timestamp <= ?
                ORDER BY next_review_timestamp ASC
                LIMIT ?
            """, (now_ts, limit))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_all_words(self) -> list[dict]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM vocab_bank ORDER BY id DESC")
            return [dict(r) for r in cursor.fetchall()]

    def review_card(self, card_id: int, quality: int):
        """
        SM-2 Algoritması:
        quality: 1 (Zor/Zayıf), 3 (İyi), 5 (Kolay/Mükemmel)
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM vocab_bank WHERE id = ?", (card_id,))
            card = cursor.fetchone()

            if not card:
                return

            ease = card["ease_factor"]
            interval = card["interval_days"]
            reps = card["repetition_count"]

            # Ease Factor hesabı
            new_ease = max(1.3, ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))

            if quality < 3:
                new_reps = 0
                new_interval = 1
            else:
                new_reps = reps + 1
                if new_reps == 1:
                    new_interval = 1
                elif new_reps == 2:
                    new_interval = 6
                else:
                    new_interval = int(interval * new_ease)

            next_ts = time.time() + (new_interval * 86400)

            cursor.execute("""
                UPDATE vocab_bank
                SET ease_factor = ?, interval_days = ?, repetition_count = ?, next_review_timestamp = ?
                WHERE id = ?
            """, (new_ease, new_interval, new_reps, next_ts, card_id))
            conn.commit()

    def delete_word(self, card_id: int):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM vocab_bank WHERE id = ?", (card_id,))
            conn.commit()
