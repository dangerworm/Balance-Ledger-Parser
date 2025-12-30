# Ledger HTR Lab — Preprocessing & Multi-Engine Specification

This document extends the existing **Ledger HTR Lab** thin-slice and defines the next iteration: a configurable preprocessing pipeline and multiple HTR engines (Dummy, Tesseract, TrOCR, Kraken) for systematic experimentation on historical handwritten ledger rows.

This spec is written to be **directly consumable by an AI coding agent (Cursor/Codex)**.

---

## 1. Purpose

The goal of this phase is to turn the HTR Lab into a **controlled experimentation bench** that allows a user to:

- Upload a single ledger page image
- Select a row-sized region
- Apply configurable image preprocessing steps
- Run multiple HTR engines on the same crop
- Visually compare raw vs preprocessed crops
- Inspect text output, confidence, and timing

This phase is explicitly exploratory and prioritises **observability and debuggability** over automation.

---

## 2. Supported HTR Engines

The backend must expose the following engines via a common interface:

### 2.1 Dummy Engine (Required)
- Always returns placeholder text
- Used to validate UI and pipeline wiring

### 2.2 Tesseract (Baseline / Comparator)
- Uses `pytesseract`
- Configuration:
  - `--oem 1` (LSTM)
  - `--psm 7` (single text line) default
- Expected to perform poorly on cursive handwriting
- Retained as a baseline reference only

### 2.3 TrOCR (Primary Baseline)
- Transformer-based OCR (HuggingFace)
- Handwritten model variant
- CPU-compatible (GPU optional)
- Used to answer: *“Is usable HTR possible without training?”*

### 2.4 Kraken (HTR-oriented Engine)
- Intended for historical documents
- Requires a model file (`.mlmodel`)
- If no model is configured, selecting Kraken must return a clear error
- Engine wiring should exist even if a model is not yet bundled

---

## 3. Preprocessing Pipeline

### 3.1 Design Principles

- Preprocessing is **explicit, ordered, and deterministic**
- UI uses checkboxes, but backend enforces a fixed execution order
- Backend returns the **applied pipeline** in the response
- Raw and preprocessed crops are both returned

### 3.2 Preprocessing Steps (Checkboxes)

UI must expose the following options:

- `grayscale`
- `contrast_stretch` (autocontrast)
- `denoise` (light median blur)
- `threshold` (mutually exclusive):
  - `none`
  - `otsu`
  - `adaptive`
- `invert`

### 3.3 Enforced Execution Order (Backend)

If enabled, preprocessing steps are applied in this order:

1. Grayscale
2. Contrast stretch
3. Denoise
4. Threshold (Otsu **or** Adaptive — never both)
5. Invert

If both threshold modes are selected, backend must:
- reject the request **or**
- enforce precedence (`adaptive` > `otsu`) and report it

---

## 4. Bounding Box Padding

HTR engines are sensitive to clipped ascenders/descenders.

The backend must support optional padding parameters:

- `pad_x` (pixels, default `0`)
- `pad_y` (pixels, default `0`)

Padding is applied symmetrically and clamped to image bounds **before preprocessing**.

---

## 5. API Specification

### 5.1 POST `/api/htr`

Run HTR on a selected region with preprocessing.

#### Request JSON
```json
{
  "image_id": "uuid",
  "bbox": { "x": 77, "y": 1022, "w": 2304, "h": 177 },
  "pad_x": 10,
  "pad_y": 5,
  "engine": "trocr",
  "preprocess": {
    "grayscale": true,
    "contrast_stretch": true,
    "denoise": false,
    "threshold": "otsu",
    "invert": false
  }
}
```

Where:
- `threshold` ∈ `"none" | "otsu" | "adaptive"`

#### Response JSON
```json
{
  "image_id": "uuid",
  "engine": "trocr",
  "bbox": { "x": 77, "y": 1022, "w": 2304, "h": 177 },
  "padding": { "pad_x": 10, "pad_y": 5 },
  "preprocess_applied": [
    "grayscale",
    "contrast_stretch",
    "threshold:otsu"
  ],
  "text": "Per transport ...",
  "confidence": 0.61,
  "elapsed_ms": 842,
  "raw_crop_url": "/api/crop/{id}?type=raw",
  "preprocessed_crop_url": "/api/crop/{id}?type=preprocessed"
}
```

#### Error Cases
- 400 invalid bbox or preprocessing config
- 404 image not found
- 422 Kraken selected but no model configured

---

## 6. Backend Implementation Requirements

### 6.1 Engine Interface

```python
class HtrResult(TypedDict):
    text: str
    confidence: float | None

class HtrEngine(Protocol):
    name: str
    def run(self, image: Image.Image) -> HtrResult: ...
```

Each engine implementation must:
- accept a PIL Image
- return text and optional confidence
- not mutate the input image

### 6.2 Preprocessing Module

Implement a dedicated module:

```
app/preprocess/pipeline.py
```

Responsibilities:
- apply ordered preprocessing
- return:
  - processed image
  - list of applied steps (strings)

### 6.3 Crop Handling

- Raw crop and preprocessed crop must be stored separately in memory
- Both must be retrievable via `/api/crop/{id}`
- Crops encoded as PNG

### 6.4 Performance Guardrails

- Backend must measure elapsed inference time per request
- If crop exceeds a configurable max size:
  - optionally downscale while preserving aspect ratio
  - report downscaling in response metadata

---

## 7. Frontend UI Requirements

### 7.1 Controls Panel

Must include:
- Engine selector (Dummy, Tesseract, TrOCR, Kraken)
- Preprocessing checkboxes
- Threshold radio buttons (None / Otsu / Adaptive)
- Padding inputs (`pad_x`, `pad_y`)
- Run HTR button (disabled while processing)

### 7.2 Result Panel

Must display:
- Recognized text
- Confidence (if available)
- Engine name
- Elapsed time
- BBox and padding values
- Raw crop preview
- Preprocessed crop preview

### 7.3 UX Behaviour

- Show spinner during inference
- Disable Run button while processing
- Persist last result until next run

---

## 8. Observability & Debugging

The UI and API must make it easy to answer:

- Was the crop correct?
- Did preprocessing help or hurt?
- Which engine performs best on this handwriting?
- Are errors coming from layout, preprocessing, or HTR?

This phase explicitly values **transparency over elegance**.

---

## 9. Acceptance Criteria

- User can toggle preprocessing steps
- Backend applies steps in fixed order
- Raw and preprocessed crops are visibly different when expected
- TrOCR produces readable (even if imperfect) output on some rows
- Tesseract output is stable but poor (baseline confirmed)
- Kraken selection behaves predictably (success or clear error)
- Elapsed time is reported

---

## 10. Scope Boundaries

Out of scope for this phase:
- Persistence to database or blob storage
- Batch processing
- Automatic layout detection
- Training or fine-tuning models

This phase exists solely to **generate insight** before scaling.

---

## 11. Outcome of This Phase

At the end of this phase, you should be able to confidently answer:

- Which preprocessing steps matter?
- Which engines are viable for 18th-century cursive?
- How sensitive is recognition to crop width and padding?

These answers directly inform the full ledger pipeline design.
