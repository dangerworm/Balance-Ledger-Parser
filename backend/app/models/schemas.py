from typing import Optional
from pydantic import BaseModel


class UploadResponse(BaseModel):
    image_id: str
    filename: str
    content_type: str
    width: int
    height: int


class BBox(BaseModel):
    x: int
    y: int
    w: int
    h: int


class PreprocessConfig(BaseModel):
    grayscale: bool = False
    binarize: bool = False


class HealthResponse(BaseModel):
    ok: bool


class TranscribedLine(BaseModel):
    """A single transcribed line from full-page transcription."""
    line_id: str
    text: str
    confidence: Optional[float]
    bbox: BBox  # Bounding box of the line
    baseline: list[list[int]]  # Baseline coordinates [[x1,y1], [x2,y2]]


class FullPageRequest(BaseModel):
    """Request for full-page transcription."""
    image_id: str
    preprocess: Optional[PreprocessConfig] = None


class FullPageResponse(BaseModel):
    """Response from full-page transcription."""
    image_id: str
    preprocess_applied: list[str]
    lines: list[TranscribedLine]
    elapsed_ms: int
    total_lines: int
