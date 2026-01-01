# Component 1 – Image Ingestion & Pre‑Processing Service (Implementation Spec)

> **Project:** Hope & Co Ledger Digitisation (c.1770)
> **Component:** 1 – Image Ingestion & Pre‑Processing Service
> **Goal:** Convert raw scanned ledger images (often two-page spreads) into clean, geometrically normalised, single-page images suitable for downstream AI processing and human review, while preserving forensic traceability.

This document is written to be directly usable by coding agents (Codex/Cursor/etc.) to implement the component end-to-end.

---

## 0. Source Specs

This implementation spec is derived from the project’s baseline overview and Component 1 spec.

- Overview: `../planning/spec-basic-overview.md`
- Component 1: `../planning/spec-component-1.md`

(These define the non-negotiables: traceability, correlation IDs, append-only storage via `IsSuperseded`, deterministic/idempotent processing, and “always emit something”.)

---

## 1. Technology Choices

### 1.1 Primary language

- **Python 3.11+**

Rationale:

- Best-in-class image processing ecosystem (OpenCV, Pillow, NumPy).
- Simple packaging and containerisation.
- Fast iteration on computer vision.

> Note: Downstream services can be C#/.NET; this component is optimised for OpenCV-heavy work.

### 1.2 Framework

Choose one (both designs below use the same internal modules):

- **Option A (recommended for a service): FastAPI**
  - Runs as a stateless HTTP service (Container Apps/App Service).
- **Option B (recommended for event-driven): Azure Functions (Python)**
  - Blob-triggered ingestion and processing.

This spec assumes **FastAPI** for clarity, but keep the internal pipeline independent of hosting.

### 1.3 Key libraries

- `opencv-python` (OpenCV)
- `numpy`
- `Pillow`
- `pydantic` (models)
- `fastapi` + `uvicorn`
- `python-multipart` (upload)
- `azure-storage-blob`
- `azure-identity` (optional; Managed Identity)
- `httpx` (if calling other internal APIs)

### 1.4 Azure services (no Terraform yet)

This component needs placeholders for:

- **Azure Blob Storage**
  - Raw images container (immutable)
  - Derived images container (cropped + normalised pages)
  - Optional: debug artefacts container
- **Queueing (optional but recommended)**
  - Azure Storage Queues or Service Bus
- **Database** (your choice)
  - Azure Database for PostgreSQL *or* Azure SQL
  - Must support append-only pattern with `IsSuperseded`.
- **Hosting**
  - Azure Container Apps / App Service / AKS / Azure Functions
- **Observability**
  - Application Insights / Log Analytics

---

## 2. Component Responsibilities

### 2.1 Inputs

- High-resolution scanned images (JPG/PNG/TIFF), typically **two-page spreads**.
- Minimal metadata:
  - `source_archive` (string)
  - `scan_batch` (string)
  - `original_filename` (string)
  - optional: `book_id`, `volume_id`

### 2.2 Outputs

For each ingested spread image:

1. **Original image** stored immutably.
2. **Spread record** in DB.
3. **Derived page images** (minimum):
   - `page_raw_crop` (cropped page from original)
   - `page_normalised` (deskewed + perspective-corrected)
4. **Page records** in DB (typically two: left and right).
5. **Bridge facts** at spread level and/or page level:
   - `left_page_id`, `right_page_id`
   - `spread_layout_type` (optional/unknown initially)
   - `gutter_x` (pixel position in original, optional)
6. **ProcessingRun record** with correlation ID.

### 2.3 Non-goals

- No semantic interpretation.
- No text extraction.
- No block segmentation.

---

## 3. API Design

### 3.1 Service base

- `BASE_URL`: `{{COMPONENT_1_BASE_URL}}`

### 3.2 Endpoints

#### POST `/v1/spreads/ingest`

Ingest one spread image (multipart upload or URL reference).

Request (multipart form):

- `file`: binary
- `metadata`: JSON string

Metadata schema:

```json
{
  "source_archive": "NL-SAA",
  "scan_batch": "735-892",
  "original_filename": "...",
  "book_id": "optional",
  "volume_id": "optional",
  "notes": "optional"
}
```

Response:

```json
{
  "correlation_id": "uuid",
  "spread_id": "uuid",
  "status": "Completed|NeedsReview|Failed",
  "warnings": ["..."],
  "pages": [
    {
      "page_id": "uuid",
      "side": "Left|Right|Unknown",
      "raw_crop_blob_uri": "...",
      "normalised_blob_uri": "...",
      "page_number_detected": "optional",
      "confidence": 0.0
    }
  ]
}
```

#### POST `/v1/spreads/ingest-by-uri`

Ingest a spread image already in Blob Storage or accessible via URL.

Request:

```json
{
  "input_uri": "https://...",
  "metadata": { ... }
}
```

#### GET `/v1/spreads/{spread_id}`

Return spread metadata, page list, processing history.

#### GET `/v1/pages/{page_id}`

Return page metadata including derivative image URIs.

#### POST `/v1/pages/{page_id}/reprocess`

Re-run preprocessing with a new `processing_version`.

Request:

```json
{
  "processing_version": "2026-01-01-a",
  "force": false
}
```

Notes:

- `force=false` should behave idempotently (if identical inputs+config exist, return existing artefacts).

---

## 4. Data Model (Logical)

> Use whatever DB you like; table names below are conceptual. Keep **append-only** semantics with `IsSuperseded`.

### 4.1 `OriginalImages`

- `Id` (UUID)
- `CorrelationId` (UUID)
- `CreatedAtUtc` (datetime)
- `CreatedByUserId` (string/uuid)
- `IsSuperseded` (bool)
- `SourceArchive` (text)
- `ScanBatch` (text)
- `OriginalFilename` (text)
- `ContentType` (text)
- `ByteLength` (int)
- `Sha256` (text)
- `BlobUri` (text)

### 4.2 `Spreads`

- `Id`
- `CorrelationId`
- `CreatedAtUtc`
- `IsSuperseded`
- `OriginalImageId` (FK)
- `ProcessingVersion` (text)
- `Status` (`Completed|NeedsReview|Failed`)
- `WarningsJson` (json)
- `GutterX` (int, nullable) – x-coordinate in original image
- `SpreadLayoutType` (text, nullable)
- `LeftPageId` (FK nullable until created)
- `RightPageId` (FK nullable until created)

### 4.3 `Pages`

- `Id`
- `CorrelationId`
- `CreatedAtUtc`
- `IsSuperseded`
- `SpreadId` (FK)
- `Side` (`Left|Right|Unknown`)
- `ProcessingVersion` (text)
- `Status` (`Completed|NeedsReview|Failed`)
- `WarningsJson` (json)
- `PageNumberDetected` (text nullable)
- `Confidence` (float 0..1)
- `RawCropBlobUri` (text)
- `NormalisedBlobUri` (text)
- `GeometryJson` (json) – detected page polygon, perspective transform matrix, etc.

### 4.4 `ProcessingRuns`

- `Id`
- `CorrelationId`
- `CreatedAtUtc`
- `Component` (text = `Component1`)
- `InputSha256` (text)
- `ProcessingVersion` (text)
- `ModelVersion` (nullable)
- `PromptVersion` (nullable)
- `Status` (`Completed|NeedsReview|Failed`)
- `WarningsJson` (json)
- `ErrorJson` (json)

---

## 5. Configuration

Use env vars (or Azure App Configuration later). Placeholders:

- `AZURE_BLOB_ACCOUNT_URL={{BLOB_ACCOUNT_URL}}`
- `AZURE_BLOB_CONTAINER_RAW={{RAW_CONTAINER_NAME}}`
- `AZURE_BLOB_CONTAINER_DERIVED={{DERIVED_CONTAINER_NAME}}`
- `AZURE_BLOB_CONTAINER_DEBUG={{DEBUG_CONTAINER_NAME}}` (optional)

Auth (choose one):

- Connection string: `AZURE_STORAGE_CONNECTION_STRING={{...}}`
- Managed Identity:
  - `AZURE_CLIENT_ID={{MANAGED_IDENTITY_CLIENT_ID}}` (optional)

Database:

- `DB_CONNECTION_STRING={{DB_CONNECTION_STRING}}`

Processing:

- `PROCESSING_VERSION=2026-01-01-a`
- `DEFAULT_MARGIN_PX=20`
- `MIN_PAGE_AREA_RATIO=0.25` (discard tiny contours)
- `MAX_PAGE_AREA_RATIO=0.98`
- `GUTTER_SEARCH_BAND_RATIO=0.15` (centre band width)
- `OUTPUT_FORMAT=png`
- `OUTPUT_DPI=300` (if emitting TIFF/PDF later)

---

## 6. Processing Pipeline (Implementation Detail)

### 6.1 Overview

Given a spread image, produce pages:

1. Load image.
2. Detect page contours.
3. Detect gutter / split line.
4. For each page candidate:
   - expand margin
   - perspective transform to rectangle
   - emit raw crop + normalised image
5. Store artefacts + metadata.
6. Always emit something; on failure emit a `NeedsReview` record with best-effort derivatives.

### 6.2 Step-by-step algorithm

#### Step A: Load & standardise

- Read image into BGR (OpenCV).
- Convert to grayscale for edge detection.
- Optional: downscale for detection (keep original for warping).

#### Step B: Page boundary detection

Goal: find the outer boundary of each page.

Suggested approach:

1. Apply `cv2.GaussianBlur`.
2. Use Canny edge detection.
3. Dilate + close gaps (`cv2.morphologyEx` with `MORPH_CLOSE`).
4. Find contours.
5. Filter contours:
   - by area ratio (`MIN_PAGE_AREA_RATIO`..`MAX_PAGE_AREA_RATIO`)
   - by aspect ratio (pages are tall rectangles)
6. Approximate each contour polygon (`cv2.approxPolyDP`).
7. Choose the best candidates:
   - Prefer 2 large page-like contours.
   - If only 1 detected, fallback to gutter split heuristic.

Edge cases:

- Single-page scans.
- Dark borders, hands, table edges.

#### Step C: Gutter detection

Goal: identify the split between left/right pages.

Heuristic options (use in order):

1. If two page contours found, infer gutter as midpoint between their bounding boxes.
2. Else, search for a vertical low-ink band near the centre:
   - take central band of width `GUTTER_SEARCH_BAND_RATIO * image_width`
   - compute column-wise ink density (sum of inverted grayscale)
   - pick the minimum-density vertical line as `gutter_x`

Store `gutter_x` for traceability.

#### Step D: Crop per side

Define left and right candidate regions using gutter + image bounds.

- Left ROI: `[0:gutter_x]`
- Right ROI: `[gutter_x:width]`

Within each ROI, attempt to detect the page contour again (more reliable locally).

If contour detection fails within ROI:

- fallback to using the ROI itself as the page boundary
- mark warnings and set status `NeedsReview`

#### Step E: Margin expansion

Expand the chosen polygon outward.

Implementation options:

- For rectangle-like polygons: expand bounding box by `DEFAULT_MARGIN_PX`.
- For general polygons: offset polygon via simple bounding box expansion first (acceptable), or use a polygon offset library later.

Clamp to image bounds.

#### Step F: Perspective correction

- Compute 4-point transform to a rectangle.
- Order points consistently (top-left, top-right, bottom-right, bottom-left).
- Choose output size:
  - based on detected edge lengths (preserve resolution)
  - optional: clamp to max dimension

Use `cv2.warpPerspective`.

Outputs:

- `raw_crop`: crop from original image using bounding box/polygon mask (no warp)
- `normalised`: warped rectangular image

#### Step G: Optional dewarping (future)

Explicitly NOT required now.

Leave an interface stub:

- `IDewarpStrategy.apply(image, metadata) -> image`

#### Step H: Page number detection (optional)

- As a placeholder, attempt a very lightweight page-number OCR in the top corners.
- This can be disabled by default.
- Output is advisory: `PageNumberDetected` + confidence.

Do NOT block the pipeline on this.

### 6.3 Warnings & degradation

This service MUST NEVER silently drop input.

If any of the following occur, output must still be stored and returned, with status `NeedsReview`:

- page boundary detection fails
- only one page detected in a spread
- gutter detection ambiguous
- perspective transform unstable

If the service crashes mid-way:

- Write a `ProcessingRun` with status `Failed` and an `ErrorJson`
- If any artefacts were produced, keep them.

---

## 7. Idempotency & Caching

### 7.1 Input hashing

Compute SHA-256 of the original image bytes.

Additionally compute a **processing fingerprint**:

- `sha256(image_bytes + processing_version + config_json)`

Use this to:

- avoid reprocessing identical inputs unless `force=true`
- return existing `SpreadId`/`PageId` records for the same fingerprint

### 7.2 Immutability

- Raw images are immutable.
- Derived images are immutable per `processing_version`.
- Reprocessing creates new records and supersedes previous ones.

---

## 8. Logging, Metrics, and Debug Artefacts

### 8.1 Logs

Emit structured logs with:

- `correlation_id`
- `spread_id`
- `page_id`
- `processing_version`
- `input_sha256`

### 8.2 Metrics

Track at minimum:

- processing time per spread
- percentage `NeedsReview`
- contour detection success rate
- average output dimensions

### 8.3 Debug artefacts (optional but recommended)

For pages that end `NeedsReview`, store debug overlays:

- original image with detected contours drawn
- gutter line drawn
- page polygon drawn

Store in debug container:

- `debug/{spread_id}/{correlation_id}/...png`

---

## 9. User Stories

### US-1: Ingest a spread image

As a user, I want to upload a scanned spread image and receive normalised single-page images, so that downstream processing and review can operate on consistent page geometry.

### US-2: Preserve forensic provenance

As a historian/reviewer, I want every derived page image to link back to the original scan and the processing configuration, so I can audit and reproduce results.

### US-3: Handle imperfect scans

As a user, I want the system to always produce a best-effort result even when page detection fails, so that no scan is silently lost.

### US-4: Reprocess with improved algorithms

As a user, I want to re-run preprocessing for an existing spread under a new processing version, so that improvements don’t destroy prior outputs and can be compared.

### US-5: Support later cross-page logic

As a downstream component, I want the spread to retain left/right page linkage and gutter metadata, so that debit/credit pairing and cross-page validation can be implemented later.

---

## 10. Acceptance Criteria

### AC-1: Basic ingestion

Given a valid spread image upload, when `/v1/spreads/ingest` is called, then:

- A `correlation_id` is returned.
- The original image is stored in the raw container.
- A spread record is created.
- At least one page record is created.
- At least one derived page image (`raw_crop` and `normalised`) is stored.

### AC-2: Two-page detection

Given a typical two-page spread, then:

- Two page records are created, with `Side=Left` and `Side=Right`.
- The spread record contains `LeftPageId` and `RightPageId`.

### AC-3: Degradation without data loss

Given a spread where page boundary detection fails, then:

- The service still returns a response.
- It stores best-effort page outputs.
- It sets status to `NeedsReview`.
- It records warnings describing what failed.

### AC-4: Idempotency

Given the same image and the same processing version/configuration, when ingest is called twice with `force=false`, then:

- The second call returns the existing spread/pages (or indicates it is a duplicate).
- No duplicate derived artefacts are stored.

### AC-5: Reprocessing

Given an existing spread, when `/v1/pages/{page_id}/reprocess` is called with a new `processing_version`, then:

- New page and artefact records are created.
- Old records are marked `IsSuperseded=true` (or equivalent soft supersede).
- Both old and new artefacts remain available for audit.

### AC-6: Provenance completeness

Every created DB row includes:

- unique row ID
- correlation ID
- created timestamp
- `IsSuperseded` flag
- FK links back to source (spread/page/original image)

### AC-7: Output image quality

The normalised page images:

- are rectangular (no trapezoid distortion)
- are deskewed based on page edges
- include a small configurable margin
- preserve original resolution as far as practical

---

## 11. Testing Strategy

### 11.1 Unit tests

- contour selection and filtering
- point ordering for perspective transform
- gutter detection on synthetic images
- idempotency hash computation

### 11.2 Golden image tests

Maintain a small corpus of representative spreads:

- clean two-page spread
- one-page scan
- dark border / partial occlusion
- heavy gutter shadow

For each:

- expected number of pages
- expected status (`Completed` vs `NeedsReview`)
- expected approximate output dimensions

### 11.3 Integration tests

- ingest endpoint writes to Blob and DB
- reprocess produces superseding records

---

## 12. Project Structure (Suggested)

```text
component1-ingestion/
  app/
    main.py                 # FastAPI entrypoint
    config.py               # env parsing
    api/
      routes_spreads.py
      routes_pages.py
    services/
      ingestion_service.py
      preprocessing_pipeline.py
      blob_store.py
      db_store.py
    cv/
      detect_pages.py
      detect_gutter.py
      warp.py
      debug_overlays.py
    models/
      dto.py                # request/response
      entities.py           # DB models
  tests/
    unit/
    golden/
    integration/
  component-1-implementation-spec.md
  requirements.txt
  README.md
```

---

## 13. Implementation Notes for Coding Agents

When implementing:

- Keep image processing pure and testable (no Azure calls inside CV functions).
- Treat all storage operations as “write-once”; use superseding rather than updates.
- Make all warnings explicit and user-visible.
- Prefer small, composable functions:
  - `detect_page_polygons(image) -> list[Polygon]`
  - `detect_gutter_x(image, polygons) -> int`
  - `normalise_page(image, polygon) -> (raw_crop, normalised, geometry)`

---

## 14. Open Questions / TODO Placeholders

These are deliberately left configurable:

- Exact DB schema and ORM choice (SQLAlchemy vs raw SQL).
- Whether to emit TIFF in addition to PNG.
- Whether to run optional page-number detection.
- Whether to store debug overlays by default.
- How to identify the “book / volume” reliably from filenames.

---

## 15. Deliverables

The implementation is complete when:

- The service runs locally.
- You can upload a spread and get normalised pages in Blob Storage.
- DB records exist with correct provenance and statuses.
- It produces meaningful `NeedsReview` outputs on failure cases.

---

## Appendix A: Placeholder Endpoints

- Blob account URL: `{{BLOB_ACCOUNT_URL}}`
- Raw container: `{{RAW_CONTAINER_NAME}}`
- Derived container: `{{DERIVED_CONTAINER_NAME}}`
- Debug container: `{{DEBUG_CONTAINER_NAME}}`
- DB connection string: `{{DB_CONNECTION_STRING}}`
- Service base URL: `{{COMPONENT_1_BASE_URL}}`
