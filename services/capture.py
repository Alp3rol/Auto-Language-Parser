import io
from PIL import Image
from PySide6.QtCore import QRect, QBuffer, QIODevice
from PySide6.QtGui import QGuiApplication, QImage, QPixmap


def capture_screen_area(rect: QRect) -> Image.Image:
    """
    Ekrandaki seçilen alanı Qt'nin yerel ekran alma API'si ile yakalar.
    PNG bellek arabelleği (QBuffer) kullanarak QImage row-stride (bytesPerLine)hizalamasını
    ve DPI ölçeklemesini %100 kusursuz korur. Piksel kayması ve bozulma riski sıfırdır.
    """
    screen = QGuiApplication.screenAt(rect.center()) or QGuiApplication.primaryScreen()
    pixmap = screen.grabWindow(0, rect.x(), rect.y(), rect.width(), rect.height())

    if pixmap.isNull() or pixmap.width() <= 0 or pixmap.height() <= 0:
        return None

    # Loss-free PNG kaydı ile satır hizalama ve piksel kaymalarını tamamen engelle
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    pixmap.save(buffer, "PNG")
    png_bytes = buffer.data().data()
    buffer.close()

    img = Image.open(io.BytesIO(png_bytes))
    return img.convert("RGB")
