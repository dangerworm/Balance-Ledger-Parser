from PIL import Image

from .base import HtrEngine, HtrResult


class DummyHtrEngine:
    name = "dummy"

    def run(self, image: Image.Image) -> HtrResult:  # noqa: ARG002
        return HtrResult(text="[dummy] recognizer placeholder", confidence=0.5)
