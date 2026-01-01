import io
import time

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from PIL import Image

from .htr.kraken_htr_engine import KrakenHtrEngine
from .models.schemas import HealthResponse, UploadResponse, FullPageRequest, FullPageResponse, TranscribedLine, BBox
from .storage.memory_store import MemoryImageStore
from .preprocess import apply_preprocessing, PreprocessConfig


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

# Initialize Kraken engine
try:
    kraken_engine = KrakenHtrEngine()
    print("Kraken engine initialized successfully")
except Exception as e:
    print(f"Failed to initialize Kraken engine: {e}")
    kraken_engine = None


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
        content_type=file.content_type or "",
        width=width,
        height=height,
    )


@app.get("/api/image/{image_id}")
async def get_image(image_id: str):
    stored = store.get_image(image_id)
    if not stored:
        raise HTTPException(status_code=404, detail="Image not found")
    return Response(content=stored.content, media_type=stored.content_type)


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(ok=True)


@app.post("/api/transcribe-page", response_model=FullPageResponse)
async def transcribe_full_page(request: FullPageRequest):
    """
    Transcribe an entire page using Kraken's automatic line segmentation.
    """
    if not kraken_engine:
        raise HTTPException(status_code=503, detail="Kraken engine not available")

    # Get the full image
    image = store.get_pil_image(request.image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # Apply preprocessing if requested
    preprocess_applied = []
    if request.preprocess:
        preprocess_config = PreprocessConfig(
            grayscale=request.preprocess.grayscale,
            binarize=request.preprocess.binarize
        )
        preprocess_result = apply_preprocessing(image, preprocess_config)
        image = preprocess_result.image
        preprocess_applied = preprocess_result.applied_steps

    # Run segmentation and recognition
    start_time = time.time()
    results = kraken_engine.segment_and_recognize(image)
    elapsed_ms = int((time.time() - start_time) * 1000)

    # Convert results to response format
    transcribed_lines = []
    for idx, result in enumerate(results):
        # Extract confidence
        all_confidences = []
        if hasattr(result, 'confidences') and result.confidences:
            all_confidences.extend(result.confidences)
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else None

        # Get bounding box from baseline
        baseline = result.baseline
        boundary = result.boundary if hasattr(result, 'boundary') else None

        # Calculate bbox from boundary or baseline
        if boundary:
            xs = [p[0] for p in boundary]
            ys = [p[1] for p in boundary]
            bbox = BBox(
                x=int(min(xs)),
                y=int(min(ys)),
                w=int(max(xs) - min(xs)),
                h=int(max(ys) - min(ys))
            )
        else:
            # Fallback to baseline if no boundary
            xs = [p[0] for p in baseline]
            ys = [p[1] for p in baseline]
            bbox = BBox(
                x=int(min(xs)),
                y=int(min(ys)),
                w=int(max(xs) - min(xs)),
                h=20  # Default height
            )

        transcribed_lines.append(TranscribedLine(
            line_id=f"line_{idx}",
            text=result.prediction,
            confidence=avg_confidence,
            bbox=bbox,
            baseline=baseline
        ))

    return FullPageResponse(
        image_id=request.image_id,
        preprocess_applied=preprocess_applied,
        lines=transcribed_lines,
        elapsed_ms=elapsed_ms,
        total_lines=len(transcribed_lines)
    )
