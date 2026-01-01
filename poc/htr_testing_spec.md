# Ledger HTR Lab — Thin Slice Specification

## Objective

Build a small web application to rapidly test Handwritten Text Recognition (HTR) on historical ledger scans by:

1. Uploading a single image
2. Selecting a rectangular region (typically a row)
3. Cropping that region server-side
4. Running HTR on the crop
5. Displaying recognized text and debug output

This is a **prototype / lab tool**, designed to validate HTR quality and UX patterns before building the full ledger pipeline.

---

## Tech Stack

- **Backend:** Python, FastAPI, Uvicorn
- **Frontend:** React + TypeScript + Vite
- **Storage:** In-memory only (no database)
- **HTR Engines:**
  - Required: Dummy engine (always works)
  - Optional: Tesseract baseline (sanity check only)

---

## Functional Requirements

### FR1 — Upload Image

- User can drag/drop or select an image file
- Supported formats: PNG, JPG, JPEG, WEBP
- Backend stores image bytes in memory
- Backend returns:
  - `image_id` (UUID)
  - filename
  - content type
  - natural width / height

### FR2 — Image Preview

- Frontend fetches image via backend URL
- Image is displayed at any size
- Natural image dimensions must be known for coordinate conversion

### FR3 — Region Selection

- User can draw a rectangular selection over the image
- Selection overlay is visible
- Selection can be cleared and redrawn
- Selection coordinates are converted to **image-native pixel space** before sending to backend

### FR4 — Run HTR

- User clicks “Run HTR”
- Frontend sends `{ image_id, bbox }` to backend
- Backend:
  - validates bbox
  - crops region from original image
  - runs HTR engine
  - returns recognized text and metadata

### FR5 — Display Output

- UI displays:
  - recognized text
  - confidence (if available)
  - engine name
  - bbox used
  - cropped image preview (recommended)

### FR6 — Error Handling

- No image → actions disabled
- No selection → “Run HTR” disabled
- Backend errors surfaced clearly in UI

---

## Non‑Functional Requirements

### Coordinate Correctness (Critical)

- All bboxes sent to backend are in **original image pixel coordinates**
- Backend clamps bbox to image bounds

### Simplicity

- No persistence
- No auth
- One image at a time per upload

### Swapability

- HTR engine must be replaceable without API changes

---

## UX Layout (Single Page)

Suggested layout:

- **Left:** Image preview with selection overlay
- **Right:**
  - Upload control
  - Engine selector
  - Run HTR button
  - Results panel

Optional keyboard shortcuts:

- `Esc` → clear selection
- `Enter` → run HTR (if selection exists)

---

## Backend API Specification

### POST `/api/upload`

Upload an image.

#### Request

- multipart/form-data
  - `file`: image

#### Response 200

```json
{
  "image_id": "uuid",
  "filename": "page22.jpg",
  "content_type": "image/jpeg",
  "width": 3000,
  "height": 2000
}
```

Errors:

- 400 invalid image
- 415 unsupported media type

---

### GET `/api/image/{image_id}`

Return original image bytes.

Errors:

- 404 image not found

---

### POST `/api/htr`

Run HTR on a selected region.

#### Request JSON

```json
{
  "image_id": "uuid",
  "bbox": { "x": 100, "y": 200, "w": 800, "h": 80 },
  "engine": "dummy"
}
```

#### Response 200

```json
{
  "image_id": "uuid",
  "engine": "dummy",
  "bbox": { "x": 100, "y": 200, "w": 800, "h": 80 },
  "text": "Per transport ...",
  "confidence": 0.75,
  "crop_image_url": "/api/crop/{crop_id}"
}
```

Errors:

- 400 invalid bbox
- 404 image not found

---

### GET `/api/crop/{crop_id}` (Recommended)

Return the cropped image for debugging.

---

### GET `/api/health`

Returns `{ "ok": true }`

---

## Backend Implementation Details

### Dependencies (`requirements.txt`)

```text
fastapi
uvicorn[standard]
pillow
python-multipart
pydantic
pytesseract
```

### In-Memory Storage

Implement `MemoryImageStore`:

- `images: Dict[image_id → {bytes, width, height, content_type}]`
- `crops: Dict[crop_id → {bytes, content_type}]`

Optional limits:

- max images: 100
- max image size: 25MB

### Cropping

- Use Pillow
- Clamp bbox to image bounds
- Reject zero/negative width or height
- Encode crops as PNG

### HTR Engine Interface

```python
class HtrResult(TypedDict):
    text: str
    confidence: float | None

class HtrEngine(Protocol):
    name: str
    def run(self, image: Image.Image) -> HtrResult: ...
```

Implement:

- `DummyHtrEngine`
- `TesseractHtrEngine` (optional)

---

## Frontend Specification

### App State

- imageId
- imageUrl
- naturalSize
- displaySize
- selectionDisplay
- selectionImageSpace
- result
- error

### Coordinate Conversion

Given:

- displayed image size from `getBoundingClientRect()`
- natural size from `img.naturalWidth / naturalHeight`

Compute:

```python
scaleX = naturalWidth / displayedWidth
scaleY = naturalHeight / displayedHeight

x = round(displayX * scaleX)
y = round(displayY * scaleY)
w = round(displayW * scaleX)
h = round(displayH * scaleY)
```

Send `{x,y,w,h}` to backend.

---

### Components

#### Dropzone

- Handles file upload

#### ImageAnnotator

- Renders image
- Handles mouse events for rectangle selection
- Draws overlay

#### Controls

- Clear selection
- Engine selector
- Run HTR

#### ResultPanel

- Displays text
- Confidence
- Bbox JSON
- Cropped image preview

---

## Repo Layout

```text
ledger-htr-lab/
  backend/
    app/
      main.py
      storage/
        memory_store.py
      htr/
        base.py
        dummy.py
        tesseract_engine.py
      models/
        schemas.py
    requirements.txt
    README.md
  frontend/
    index.html
    vite.config.ts
    package.json
    src/
      main.tsx
      App.tsx
      api.ts
      components/
        Dropzone.tsx
        ImageAnnotator.tsx
        Controls.tsx
        ResultPanel.tsx
    README.md
  README.md
```

---

## Development Setup

### Backend

```bash
python -m venv .venv
source .venv/bin/activate  # or Windows equivalent
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
npm install
npm run dev
```

---

## Acceptance Criteria

- Image upload works
- Image preview displays correctly
- Rectangle selection works
- Bbox conversion is correct
- Backend crops correct region
- HTR output is returned and shown
- Cropped preview matches selection

---

## Optional Enhancements (Later)

- Multiple selections per image
- PDF support (render first page)
- Preprocessing toggles (threshold/contrast)
- Persist uploads to disk or blob storage
- Token-level confidence display

---

## Purpose of This Tool

This HTR Lab exists to:

- Validate handwriting recognition quality early
- Debug cropping and coordinate handling
- Establish the review UX pattern used later in the full ledger system

It is intentionally small, disposable, and fast to iterate.
