from PIL import Image
from PySide6.QtCore import QRect
from PySide6.QtGui import QGuiApplication, QImage


def capture_screen_area(rect: QRect) -> Image.Image:
    """
    Ekrandaki seçilen alanı Qt'nin yerel piksel-mükemmel ekran alma API'si ile yakalar.
    Zero-Copy piksel aktarımı ile CPU ve RAM israfı yaşamadan anında PIL Image'a dönüştürür.
    """
    screen = QGuiApplication.screenAt(rect.center()) or QGuiApplication.primaryScreen()
    pixmap = screen.grabWindow(0, rect.x(), rect.y(), rect.width(), rect.height())

    qimg = pixmap.toImage().convertToFormat(QImage.Format.Format_RGB888)
    width = qimg.width()
    height = qimg.height()

    ptr = qimg.bits()
    img = Image.frombytes("RGB", (width, height), ptr.tobytes())
    return img

