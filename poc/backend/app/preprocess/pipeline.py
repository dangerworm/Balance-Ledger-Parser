"""
Image preprocessing pipeline for HTR experiments.

Applies transformations in a fixed order:
1. Grayscale
2. Binarize (Otsu thresholding)
"""
from PIL import Image, ImageOps
import numpy as np
import cv2


class PreprocessConfig:
    """Configuration for preprocessing pipeline."""

    def __init__(
        self,
        grayscale: bool = False,
        binarize: bool = False,
    ):
        self.grayscale = grayscale
        self.binarize = binarize


class PreprocessResult:
    """Result of preprocessing pipeline."""

    def __init__(self, image: Image.Image, applied_steps: list[str]):
        self.image = image
        self.applied_steps = applied_steps


def apply_preprocessing(image: Image.Image, config: PreprocessConfig) -> PreprocessResult:
    """
    Apply preprocessing steps in fixed order.

    Args:
        image: Input PIL Image
        config: Preprocessing configuration

    Returns:
        PreprocessResult with processed image and list of applied steps
    """
    img = image.copy()
    applied_steps: list[str] = []

    # Step 1: Grayscale
    if config.grayscale:
        img = ImageOps.grayscale(img)
        applied_steps.append("grayscale")

    # Step 2: Binarize (Otsu threshold)
    if config.binarize:
        # Convert to numpy for cv2 operations
        img_array = np.array(img)

        # Ensure grayscale for thresholding
        if len(img_array.shape) == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

        _, img_array = cv2.threshold(
            img_array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        applied_steps.append("binarize")

        img = Image.fromarray(img_array)

    return PreprocessResult(image=img, applied_steps=applied_steps)


    # Step 5: Invert
    if config.invert:
        img = ImageOps.invert(img)
        applied_steps.append("invert")

    return PreprocessResult(img, applied_steps)
