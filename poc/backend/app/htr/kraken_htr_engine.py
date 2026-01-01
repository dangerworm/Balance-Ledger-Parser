"""Kraken engine for historical document HTR."""
import os
from PIL import Image
from kraken import rpred
from kraken import pageseg
from kraken.lib import models

from .base import HtrEngine, HtrResult


class KrakenHtrEngine:
    """
    Kraken HTR engine for historical documents.

    Requires a trained model file (.mlmodel).
    If no model is configured, raises an error on initialization.
    """

    name = "kraken"

    def __init__(self, model_path: str | None = None):
        """
        Initialize Kraken engine.

        Args:
            model_path: Path to .mlmodel file. If None, checks KRAKEN_MODEL_PATH env var.

        Raises:
            ValueError: If no model is configured
            FileNotFoundError: If model file doesn't exist
        """
        if model_path is None:
            # Default to the downloaded model if not specified
            from pathlib import Path
            default_model = str(Path(__file__).parent.parent.parent / "models" / "en_best.mlmodel")
            model_path = os.getenv("KRAKEN_MODEL_PATH", default_model)

        if not model_path:
            raise ValueError(
                "Kraken model not configured. Set KRAKEN_MODEL_PATH environment variable "
                "or provide model_path parameter."
            )

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Kraken model file not found: {model_path}")

        self.model_path = model_path
        self.model = models.load_any(model_path)

    def run(self, image: Image.Image) -> HtrResult:
        """
        Run Kraken recognition on the input image.

        Args:
            image: PIL Image containing text line

        Returns:
            HtrResult with recognized text and confidence
        """
        from kraken.containers import Segmentation, BaselineLine

        # For a single line image, create a simple baseline covering the full width
        # Kraken needs baseline bounds to know where the text line is
        width, height = image.size
        baseline = [(0, height // 2), (width, height // 2)]
        boundary = [(0, 0), (width, 0), (width, height), (0, height)]

        # Create a baseline line object with required id
        line = BaselineLine(
            id='line_0',
            baseline=baseline,
            boundary=boundary,
            text='',
            tags=None
        )

        # Create segmentation with the single line
        bounds = Segmentation(
            type='baselines',
            imagename="",
            text_direction='horizontal-lr',
            script_detection=False,
            lines=[line]
        )

        # Use rpred for recognition with our baseline
        results = list(rpred.rpred(
            network=self.model,
            im=image,
            bounds=bounds
        ))

        if not results:
            return HtrResult(text="", confidence=None)

        # Concatenate all recognized text
        text = " ".join(result.prediction for result in results)

        # Average confidence if available - note: Kraken uses 'confidences' (plural)
        all_confidences = []
        for result in results:
            if hasattr(result, 'confidences') and result.confidences:
                all_confidences.extend(result.confidences)

        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else None

        return HtrResult(text=text.strip(), confidence=avg_confidence)

    def segment_and_recognize(self, image: Image.Image):
        """
        Segment full page and recognize all text lines.

        Args:
            image: PIL Image of full page

        Returns:
            List of recognition results with baselines and bounding boxes
        """
        from pathlib import Path
        from kraken import blla
        from kraken.containers import Segmentation

        # Load segmentation model
        seg_model_path = Path(__file__).parent.parent.parent / "models" / "blla.mlmodel"

        try:
            seg_model = models.load_any(str(seg_model_path))
            # Verify it's a segmentation model, not a recognition model
            # Check if the model is a VGSL segmentation model
            if seg_model.__class__.__name__ not in ['TorchVGSLModel', 'TorchSegRecognizer']:
                print(f"Model at {seg_model_path} is not a valid segmentation model")
                seg_model = None
            # Additional check: ensure it's not a sequence recognizer
            if seg_model and seg_model.__class__.__name__ == 'TorchSeqRecognizer':
                print(f"Model at {seg_model_path} is a recognition model, not a segmentation model")
                seg_model = None
        except Exception as e:
            print(f"Failed to load custom segmentation model: {e}")
            print("Using default blla segmentation...")
            seg_model = None

        # Convert image to binary (required by Kraken 5's pageseg.segment)
        from PIL import ImageOps
        # Convert to grayscale first
        if image.mode != 'L':
            image_gray = image.convert('L')
        else:
            image_gray = image

        # Convert to binary using Otsu's method
        image_binary = image_gray.point(lambda x: 0 if x < 128 else 255, '1')

        # Segment the binary image
        segmentation: Segmentation = pageseg.segment(image_binary)

        # Run recognition on all detected lines using the original image
        results = list(rpred.rpred(
            network=self.model,
            im=image,
            bounds=segmentation
        ))

        return results
