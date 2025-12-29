from typing import Optional

import pytesseract
from PIL import Image

from .base import HtrEngine, HtrResult


class TesseractHtrEngine:
    name = "tesseract"

    def run(self, image: Image.Image) -> HtrResult:
        data: Optional[dict] = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        text = "".join(data.get("text", [])) if data else ""
        confidences = data.get("conf", []) if data else []
        numeric_conf = [float(c) for c in confidences if c != "-1"] if confidences else []
        avg_conf = sum(numeric_conf) / len(numeric_conf) / 100 if numeric_conf else None
        return HtrResult(text=text.strip(), confidence=avg_conf)
