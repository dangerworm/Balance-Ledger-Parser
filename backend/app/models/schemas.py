from typing import Optional
from pydantic import BaseModel, Field


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


class HtrRequest(BaseModel):
    image_id: str
    bbox: BBox
    engine: str = Field(default="dummy")


class HtrResponse(BaseModel):
    image_id: str
    engine: str
    bbox: BBox
    text: str
    confidence: Optional[float]
    crop_image_url: str


class HealthResponse(BaseModel):
    ok: bool
