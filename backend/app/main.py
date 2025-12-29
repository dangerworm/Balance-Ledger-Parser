import io
from typing import Dict

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from PIL import Image

from .htr.base import HtrEngine
from .htr.dummy import DummyHtrEngine
from .htr.tesseract_engine import TesseractHtrEngine
from .models.schemas import BBox, HealthResponse, HtrRequest, HtrResponse, UploadResponse
from .storage.memory_store import MemoryImageStore


ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}

app = FastAPI(title="Ledger HTR Lab")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


store = MemoryImageStore()
htr_engines: Dict[str, HtrEngine] = {
    "dummy": DummyHtrEngine(),
    "tesseract": TesseractHtrEngine(),
}


def validate_bbox(bbox: BBox) -> None:
    if bbox.w <= 0 or bbox.h <= 0:
        raise HTTPException(status_code=400, detail="Invalid bbox dimensions")
    if bbox.x < 0 or bbox.y < 0:
        raise HTTPException(status_code=400, detail="Invalid bbox position")


@app.post("/api/upload", response_model=UploadResponse)
async def upload_image(file: UploadFile = File(...)) -> UploadResponse:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported media type")
    content = await file.read()
    try:
        image = Image.open(io.BytesIO(content))
        width, height = image.size
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Invalid image") from exc

    image_id = store.save_image(content, width, height, file.content_type)
    return UploadResponse(
        image_id=image_id,
        filename=file.filename or "",
        content_type=file.content_type,
        width=width,
        height=height,
    )


@app.get("/api/image/{image_id}")
async def get_image(image_id: str):
    stored = store.get_image(image_id)
    if not stored:
        raise HTTPException(status_code=404, detail="Image not found")
    return Response(content=stored.content, media_type=stored.content_type)


@app.get("/api/crop/{crop_id}")
async def get_crop(crop_id: str):
    stored = store.get_crop(crop_id)
    if not stored:
        raise HTTPException(status_code=404, detail="Crop not found")
    return Response(content=stored.content, media_type=stored.content_type)


@app.post("/api/htr", response_model=HtrResponse)
async def run_htr(request: HtrRequest) -> HtrResponse:
    validate_bbox(request.bbox)
    stored = store.get_image(request.image_id)
    if not stored:
        raise HTTPException(status_code=404, detail="Image not found")

    image = Image.open(io.BytesIO(stored.content))
    x, y, w, h = store.clamp_bbox(request.bbox.x, request.bbox.y, request.bbox.w, request.bbox.h, image)
    if w <= 0 or h <= 0:
        raise HTTPException(status_code=400, detail="Invalid bbox after clamping")

    crop = image.crop((x, y, x + w, y + h))
    engine = htr_engines.get(request.engine)
    if not engine:
        raise HTTPException(status_code=400, detail="Unsupported engine")

    result = engine.run(crop)
    crop_bytes_io = io.BytesIO()
    crop.save(crop_bytes_io, format="PNG")
    crop_bytes = crop_bytes_io.getvalue()
    crop_id = store.save_crop(crop_bytes, "image/png")

    return HtrResponse(
        image_id=request.image_id,
        engine=engine.name,
        bbox=BBox(x=x, y=y, w=w, h=h),
        text=result.get("text", ""),
        confidence=result.get("confidence"),
        crop_image_url=f"/api/crop/{crop_id}",
    )


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(ok=True)
