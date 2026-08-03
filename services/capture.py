import io
import mss
from PIL import Image
from PySide6.QtCore import QBuffer, QIODevice, QRect
from PySide6.QtGui import QGuiApplication


def capture_screen_area(rect: QRect) -> Image.Image:
    """
    Ekrandaki seçilen alanı Qt'nin yerel piksel-mükemmel ekran alma API'si ile yakalar.
    Windows DPI scaling (%125, %150) kaymalarını %100 önler ve tam alanı kırpar.
    """
    # Seçim alanının merkezindeki ekranı bul
    screen = QGuiApplication.screenAt(rect.center()) or QGuiApplication.primaryScreen()
    
    # Qt yerel ekran yakalama metodu (DPI kayması yaşanmaz)
    pixmap = screen.grabWindow(0, rect.x(), rect.y(), rect.width(), rect.height())

    # QPixmap nesnesini doğrudan RAM belleğinde PIL (Pillow) Image nesnesine dönüştür
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.ReadWrite)
    pixmap.save(buffer, "PNG")

    image_bytes = bytes(buffer.data())
    buffer.close()

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return img
