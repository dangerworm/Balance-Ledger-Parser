import uuid
from dataclasses import dataclass
from typing import Dict, Optional

from PIL import Image


@dataclass
class StoredImage:
    content: bytes
    width: int
    height: int
    content_type: str


@dataclass
class StoredCrop:
    content: bytes
    content_type: str


class MemoryImageStore:
    def __init__(self, max_images: int = 100):
        self.images: Dict[str, StoredImage] = {}
        self.crops: Dict[str, StoredCrop] = {}
        self.max_images = max_images

    def save_image(self, content: bytes, width: int, height: int, content_type: str) -> str:
        if len(self.images) >= self.max_images:
            # Remove oldest inserted image to keep memory bounded
            self.images.pop(next(iter(self.images)))
        image_id = str(uuid.uuid4())
        self.images[image_id] = StoredImage(content=content, width=width, height=height, content_type=content_type)
        return image_id

    def get_image(self, image_id: str) -> Optional[StoredImage]:
        return self.images.get(image_id)

    def save_crop(self, content: bytes, content_type: str) -> str:
        crop_id = str(uuid.uuid4())
        self.crops[crop_id] = StoredCrop(content=content, content_type=content_type)
        return crop_id

    def get_crop(self, crop_id: str) -> Optional[StoredCrop]:
        return self.crops.get(crop_id)

    def clamp_bbox(self, x: int, y: int, w: int, h: int, image: Image.Image) -> tuple[int, int, int, int]:
        width, height = image.size
        x = max(0, min(x, width))
        y = max(0, min(y, height))
        w = max(0, min(w, width - x))
        h = max(0, min(h, height - y))
        return x, y, w, h
