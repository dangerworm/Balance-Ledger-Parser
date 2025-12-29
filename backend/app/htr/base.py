from typing import Protocol, TypedDict
from PIL import Image


class HtrResult(TypedDict):
    text: str
    confidence: float | None


class HtrEngine(Protocol):
    name: str

    def run(self, image: Image.Image) -> HtrResult:
        ...
