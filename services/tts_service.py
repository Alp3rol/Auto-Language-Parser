import os
import tempfile
import threading
from PySide6.QtCore import QObject, Signal, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput


class TTSService(QObject):
    """
    gTTS (Google Text-To-Speech) ve Windows SAPI5 ile
    Türkçe ve İngilizce metinleri doğal ses tonuyla sesli okuyan servis.
    """
    error = Signal(str)

    def __init__(self):
        super().__init__()
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(1.0)

    def speak(self, text: str, lang: str = "tr"):
        """
        Verilen metni belirtilen dilde ('tr' veya 'en') sesli okur.
        """
        if not text or not text.strip():
            return

        def _speak_thread():
            try:
                from gtts import gTTS
                clean_lang = "tr" if lang.lower().startswith("tr") else "en"
                tts = gTTS(text=text, lang=clean_lang, slow=False)
                
                temp_dir = tempfile.gettempdir()
                temp_file = os.path.join(temp_dir, "alp_tts_speech.mp3")
                tts.save(temp_file)

                # QMediaPlayer ile sesi çal
                self.player.stop()
                self.player.setSource(QUrl.fromLocalFile(temp_file))
                self.player.play()
            except Exception:
                # İnternet olmadığı durumlarda yerel Windows SAPI5 offline ses motorunu kullan
                try:
                    import win32com.client
                    speaker = win32com.client.Dispatch("SAPI.SpVoice")
                    speaker.Speak(text)
                except Exception as sapi_err:
                    self.error.emit(f"Metin okuma hatası: {sapi_err}")

        threading.Thread(target=_speak_thread, daemon=True).start()
