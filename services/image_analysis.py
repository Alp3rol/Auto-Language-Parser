from PIL import Image, ImageStat
from PySide6.QtGui import QColor


def extract_dominant_bg_color(pil_image: Image.Image) -> QColor:
    """
    Kırpılan ekran görüntüsünün kenarlarından ve köşelerinden baskın arka plan RGB rengini hesaplar.
    """
    if pil_image is None:
        return QColor(24, 24, 27)

    try:
        img_rgb = pil_image.convert("RGB")
        w, h = img_rgb.size
        if w < 4 or h < 4:
            return QColor(24, 24, 27)

        # Görüntü kenarlarından piksel örneklemesi yap
        border_pixels = []
        # Üst ve alt kenar
        for x in range(0, w, max(1, w // 20)):
            border_pixels.append(img_rgb.getpixel((x, 0)))
            border_pixels.append(img_rgb.getpixel((x, h - 1)))
        # Sol ve sağ kenar
        for y in range(0, h, max(1, h // 20)):
            border_pixels.append(img_rgb.getpixel((0, y)))
            border_pixels.append(img_rgb.getpixel((w - 1, y)))

        if not border_pixels:
            return QColor(24, 24, 27)

        # Ortalama R, G, B hesapla
        avg_r = int(sum(p[0] for p in border_pixels) / len(border_pixels))
        avg_g = int(sum(p[1] for p in border_pixels) / len(border_pixels))
        avg_b = int(sum(p[2] for p in border_pixels) / len(border_pixels))

        return QColor(avg_r, avg_g, avg_b)
    except Exception:
        return QColor(24, 24, 27)


def get_contrast_text_color(bg_color: QColor) -> QColor:
    """
    Arka plan rengine göre maksimum okunabilirlik için zıt metin rengi (Beyaz / Siyah) döndürür.
    Luminance formülü: 0.299*R + 0.587*G + 0.114*B
    """
    luminance = (0.299 * bg_color.red() + 0.587 * bg_color.green() + 0.114 * bg_color.blue())
    if luminance > 128:
        return QColor(15, 23, 42)  # Koyu metin (Açık temalar için)
    else:
        return QColor(248, 250, 252)  # Açık metin (Koyu temalar için)
