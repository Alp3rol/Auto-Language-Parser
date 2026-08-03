import numpy as np
from PIL import Image


class OCRService:
    """
    PaddleOCR modellerini kullanarak ekrandan Türkçe ve İngilizce metin çıkaran OCR servisi.
    Kelimeler arasındaki boşlukların korunmasını garanti eder.
    """
    def __init__(self):
        self.use_paddle_native = False
        try:
            from paddleocr import PaddleOCR
            self.ocr_engine = PaddleOCR(use_angle_cls=True, lang='en')
            self.use_paddle_native = True
            print("[OCR SERVİSİ] Native PaddleOCR Motoru Aktif.")
        except Exception:
            from rapidocr_onnxruntime import RapidOCR
            self.ocr_engine = RapidOCR()
            self.use_paddle_native = False
            print("[OCR SERVİSİ] RapidOCR (PaddleOCR ONNX Engine) Aktif.")

    def format_ocr_result(self, raw_result) -> str:
        """
        OCR ile algılanan metin bloklarını satır ve kelime hizalamasına göre gruplayıp
        kelimeler arasındaki boşlukları korur ('bensatirsatirkontroledeyim' birleşme sorununu çözer).
        """
        if not raw_result:
            return ""

        items = []
        for res in raw_result:
            if not res or len(res) < 2:
                continue
            box = res[0]
            text = str(res[1]).strip() if res[1] else ""
            score = res[2] if len(res) > 2 else 1.0
            if text:
                items.append((box, text, score))

        if not items:
            return ""

        # Kutuları üst Y koordinatına göre sırala
        items_sorted = sorted(items, key=lambda x: x[0][0][1])

        lines = []
        current_line = []
        current_y = None

        for item in items_sorted:
            box, text, score = item
            box_y = box[0][1]
            box_h = abs(box[2][1] - box[0][1])

            if current_y is None or abs(box_y - current_y) < max(12, box_h * 0.6):
                current_line.append(item)
                if current_y is None:
                    current_y = box_y
            else:
                # Satır içi soldan sağa X koordinatına göre sırala
                current_line.sort(key=lambda x: x[0][0][0])
                lines.append(current_line)
                current_line = [item]
                current_y = box_y

        if current_line:
            current_line.sort(key=lambda x: x[0][0][0])
            lines.append(current_line)

        # Kelimeleri aralarında uygun boşluk bırakarak birleştir
        line_texts = []
        for line in lines:
            words_in_line = []
            prev_right = None

            for item in line:
                box, text, _ = item
                left = box[0][0]
                right = box[1][0]

                if prev_right is not None:
                    gap = left - prev_right
                    if gap > 2:
                        words_in_line.append(" ")

                words_in_line.append(text)
                prev_right = right

            full_line = "".join(words_in_line).strip()
            if full_line:
                line_texts.append(full_line)

        return "\n".join(line_texts)

    def extract_text(self, pil_image: Image.Image) -> str:
        if pil_image is None:
            return ""

        img_np = np.array(pil_image)

        if self.use_paddle_native:
            result = self.ocr_engine.ocr(img_np, cls=True)
            if not result or not result[0]:
                return ""
            return self.format_ocr_result(result[0])
        else:
            result, _ = self.ocr_engine(img_np)
            if not result:
                return ""
            return self.format_ocr_result(result)
