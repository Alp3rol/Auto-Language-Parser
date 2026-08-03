# A.L.P. (Auto Language Parser) 🌐

**A.L.P.** (Auto Language Parser), Windows 11 için geliştirilmiş, ekranınızdaki herhangi bir İngilizce veya Türkçe metni anında seçip OCR ile okuyan ve dilini otomatik algılayarak çeviren modern bir masaüstü ekran çeviri uygulamasıdır.

---

## 🌟 Öne Çıkan Özellikler

* **🚀 Hızlı & Kararmayan Seçim Aracı**: `Alt + S` veya `F8` kısayoluyla ekran kararmadan yalnızca seçtiğiniz alanın şeffaf çerçevesini gösterir.
* **📐 Windows High-DPI Scaling Desteği**: %125 veya %150 ekran ölçeklendirmesinde dahi piksel-mükemmel kırpma yapar.
* **🔍 PaddleOCR Entegrasyonu**: Görsellerdeki metinleri yüksek doğrulukla ve kelime boşluklarını koruyarak okur.
* **🌐 Otomatik Dil Tahmini & Çeviri**: Metnin dilini otomatik algılar (İngilizce ise Türkçeye, Türkçe ise İngilizceye çevirir).
* **✨ Modern Popup Penceresi**: Çeviri sonucu, seçtiğiniz alanın hemen yanında `12px border-radius` ve koyu yarı saydam şık bir popup penceresinde belirir ve **5 saniye sonra otomatik kaybolur**.
* **🔔 Sistem Tepsisi (System Tray) Entegrasyonu**: Uygulama sistem tepsisinde çalışır ve boşta %0 CPU kullanır.

---

## 🛠️ Teknolojiler

* **Python 3.11**
* **PySide6** (Qt6 GUI)
* **pynput** (Global Keyboard Hotkey Hook)
* **mss** & **Pillow** (Screen Capture & Image Processing)
* **PaddleOCR** & **RapidOCR ONNX** (OCR Engine)
* **requests** (LibreTranslate API Integration)

---

## 💻 Kurulum ve Çalıştırma

### 1-Tıkla Çalıştırma (Windows Batch)
Proje klasöründeki `run.bat` dosyasına çift tıklayarak uygulamayı anında başlatabilirsiniz.

### Manuel Komut Satırı İle:
```powershell
# Bağımlılıkları yükleyin
pip install -r requirements.txt

# Uygulamayı başlatın
python main.py
```

---

## ⌨️ Kullanım Kısayolları

| Kısayol | Açıklama |
| :--- | :--- |
| **`Alt + S`** | Ekran seçim arayüzünü açar. |
| **`F8`** | Alternatif tek tuşla seçim arayüzünü açar. |
| **`ESC`** | Seçim modunu iptal eder. |

---

## 📜 Lisans
MIT License © 2026 Alp3rol - A.L.P. (Auto Language Parser)
