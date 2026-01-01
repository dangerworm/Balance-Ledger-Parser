# Dutch Ledger Digitisation App (1700s) — Detailed Specification (Cursor/Codex Ready)

## 1. Goal

Build a web application that ingests scanned images of Dutch handwritten accounting ledgers (1700s), automatically extracts structured line-item tables, supports rapid human correction, and exports corrected data to CSV/JSON. The system must scale to **tens of thousands of pages** and support **reprocessing** as models improve.

Key principles:

- **Pipeline, not monolith**: image → layout → text → parse → table → review → export.
- **Human-in-the-loop**: machine drafts; humans correct; corrections become training data.
- **Versioned artifacts**: every step is stored and reproducible.
- **Modular + replaceable**: swap layout/HTR engines without rewriting the app.

Non-goals (MVP):

- Fully automated 100% accurate extraction.
- Automated translation.
- Cross-ledger entity resolution beyond basic suggestions.

## 2. Primary Use Cases

1. **Ingest**: User uploads page images (single or batch). System creates Page records.
2. **Process**: Pipeline generates normalized images, layout JSON, row crops, HTR draft text, parsed fields.
3. **Review**: User reviews extracted rows, edits fields quickly, and marks page “validated”.
4. **Export**: User exports validated data to CSV/JSON with selectable schemas.
5. **Reprocess**: Admin can re-run a newer model version on selected pages and compare diffs.

## 3a. Roles & Permissions (MVP)

- **Admin**: manage projects, model versions, pipeline settings, reprocessing; review and correct extracted rows; export; view pages; view results.

## 3b. Roles & Permissions (Full version)

- **Admin**: manage projects, model versions, pipeline settings, reprocessing
- **Editor**: review and correct extracted rows, export.
- **Viewer**: view pages/results only.

Authentication: support for Azure AD optional later.

## 4. System Architecture

### 4.1 Services

- **Web App**
  - React/TypeScript frontend
  - .NET API backend (C#)
  - Postgres database
  - Blob storage for images and derived artifacts

- **Processing Workers (Python)**
  - Image preprocessing
  - Layout analysis
  - Row cropping
  - HTR inference
  - Parsing/normalization

### 4.2 Communication Pattern

- Backend queues work items (jobs).
- Workers pull jobs, produce artifacts, update DB.

Recommended MVP job runner:

- **Hangfire** in .NET for orchestration, retries, status.
- Workers expose a **HTTP API** or consume a queue (Azure Storage Queue / RabbitMQ).

Choose one:

- Option A (simple): .NET calls worker HTTP endpoints (sync for small, async for large).
- Option B (robust): queue-based with at-least-once delivery.

## 5. Pipeline Stages (Artifact Model)

Each stage writes a **versioned artifact** linked to a Page.

Stages:

1. **Ingest**: store original image.
2. **Preprocess**: normalized image (deskew/crop/contrast).
3. **Layout**: detect page split + table regions + rows + columns.
4. **Crop**: generate row-level image crops.
5. **HTR**: run handwriting text recognition on row crops.
6. **Parse**: interpret text into structured fields.
7. **Assemble**: emit extracted table rows.

All artifacts include:

- artifact_type
- model_version (if applicable)
- parameters
- created_at
- storage_uri
- checksum

## 6. Data Model (Postgres)

### 6.1 Entities

#### projects

- id (uuid, pk)
- name
- description
- created_at

#### documents (ledger volumes)

- id (uuid)
- project_id (fk)
- title
- reference_code (optional)
- date_range_start/date_range_end (optional)

#### pages

- id (uuid)
- document_id (fk)
- page_number (int)
- source_filename
- status (enum: uploaded, processing, needs_review, validated, exported, error)
- created_at

#### page_artifacts

- id (uuid)
- page_id (fk)
- artifact_type (enum: original_image, normalized_image, layout_json, row_crop, htr_text, parsed_json, assembled_rows_json)
- model_name (text, nullable)
- model_version (text, nullable)
- parameters_json (jsonb)
- storage_uri (text)
- checksum (text)
- created_at

#### extracted_rows

- id (uuid)
- page_id (fk)
- row_index (int)
- region_bbox (jsonb)  // [x,y,w,h] in normalized image coords
- confidence (float)
- status (enum: draft, corrected, validated)
- created_at

#### extracted_fields

- id (uuid)
- extracted_row_id (fk)
- field_name (text) // e.g. date, counterparty, description, amount_1, amount_2...
- value_raw (text)
- value_normalized (text)
- confidence (float)
- source (enum: model, rule, user)
- updated_at

#### corrections (audit)

- id (uuid)
- extracted_field_id (fk)
- previous_value
- new_value
- user_id
- created_at

#### model_registry (optional but recommended)

- id (uuid)
- model_name
- version
- description
- created_at

### 6.2 Notes

- Keep **raw** + **normalized** values.
- Never overwrite without auditing.
- Store bboxes in a consistent coordinate space (e.g., normalized_image pixel coords).

## 7. Layout JSON Schema

Store as artifact `layout_json`.

```json
{
  "page_id": "...",
  "image": {"width": 3000, "height": 2000},
  "splits": [{"name": "left", "bbox": [0,0,1500,2000]}, {"name": "right", "bbox": [1500,0,1500,2000]}],
  "tables": [
    {
      "table_id": "t1",
      "bbox": [100,120,1300,1700],
      "columns": [
        {"name": "ref", "bbox": [100,120,150,1700]},
        {"name": "name", "bbox": [250,120,700,1700]},
        {"name": "amount_a", "bbox": [980,120,180,1700]},
        {"name": "amount_b", "bbox": [1160,120,180,1700]}
      ],
      "rows": [
        {"row_index": 0, "bbox": [100,140,1200,40]},
        {"row_index": 1, "bbox": [100,180,1200,40]}
      ]
    }
  ],
  "totals": [{"label": "Transportee", "bbox": [900,1850,800,120]}]
}
```

## 8. HTR Output Schema

Artifact `htr_text` per row OR per page.

```json
{
  "page_id": "...",
  "rows": [
    {
      "row_index": 0,
      "text": "Jan ... Per transport ...",
      "tokens": [{"t":"Jan","c":0.91},{"t":"...","c":0.40}],
      "confidence": 0.78
    }
  ]
}
```

## 9. Parsing & Normalisation

### 9.1 Currency/Amount Parsing

Implement a parser that:

- accepts formats like `1234 10 8`, `1234.10.8`, `123.45`, `1234-`, `—`, `0`, etc.
- outputs numeric components in separate fields:
  - pounds (int)
  - shillings (int)
  - pence (int)

Rules:

- Preserve raw string as captured.
- If uncertain, set low confidence and require review.

### 9.2 Date Parsing

- Detect explicit dates (e.g., “Amsterdam 31 December 1770”).
- Support Dutch month names/abbreviations.
- Normalise to ISO `YYYY-MM-DD` where possible.

### 9.3 Names & Canonical Suggestions

- Store **as-written** string.
- Provide separate `canonical_name_suggestion` generated by:
  - simple normalization (casefold, strip punctuation, common ligature cleanup)
  - optional fuzzy matching to existing names in same project.
- Never merge automatically; suggestions only.

## 10. Review UI Requirements

### 10.1 Page Viewer

- Show full page image (zoom/pan).
- Overlay detected rows/columns.
- Click a row to open row editor.

### 10.2 Row Review Panel

For selected row:

- Show row crop image.
- Show editable fields (ref/name/description/amount columns etc.).
- Show confidence indicators.
- Keyboard-first navigation:
  - Enter = save + next row
  - Shift+Enter = save + previous row
  - Tab cycles fields
  - Hotkey to mark row “validated”

### 10.3 Page Workflow

- Page status transitions:
  - uploaded → processing → needs_review → validated
- “Validate page” requires all rows validated OR user confirms.

### 10.4 Canonicalization Tool

- List all distinct name spellings encountered.
- Allow user to pick a canonical label and associate spellings.
- Store mapping table:
  - project_id, canonical_name, variant_name

## 11. Export Requirements

Exports must be reproducible:

- export includes project/document/page ranges
- export includes schema version

Export formats:

- CSV (flat rows)
- JSON (structured)

CSV columns (default):

- project
- document
- page_number
- row_index
- ref
- counterparty_raw
- counterparty_canonical (if mapped)
- description
- amount_major
- amount_minor
- amount_subminor
- amount_raw
- row_confidence
- validated_by
- validated_at

## 12. Processing Jobs

### 12.1 Job Types

- preprocess_page
- detect_layout
- crop_rows
- htr_rows
- parse_rows
- assemble_rows

Each job has:

- job_id
- page_id
- job_type
- status
- attempts
- error_message
- started_at/finished_at

### 12.2 Retry Policy

- Retry transient failures up to N times.
- Fail permanently with error status and surface in UI.

## 13. APIs (Backend)

### 13.1 Ingest

- POST /api/projects/{projectId}/documents
- POST /api/documents/{documentId}/pages/upload (multipart)
- GET /api/pages/{pageId}

### 13.2 Processing

- POST /api/pages/{pageId}/process (enqueue full pipeline)
- POST /api/pages/reprocess (body: {pageIds:[], modelVersions:{...}})
- GET /api/pages/{pageId}/artifacts

### 13.3 Review

- GET /api/pages/{pageId}/rows
- PUT /api/rows/{rowId}/fields
- POST /api/pages/{pageId}/validate

### 13.4 Export

- POST /api/exports (filters)
- GET /api/exports/{exportId}/download

## 14. Worker Interface (Python)

Define a simple contract for each stage.

Option A: HTTP endpoints on worker

- POST /worker/preprocess {page_id, input_uri} → {artifact_uri, meta}
- POST /worker/layout {page_id, normalized_uri} → {layout_uri}
- POST /worker/crop {page_id, normalized_uri, layout_uri} → {row_crop_uris[]}
- POST /worker/htr {page_id, row_crop_uris[]} → {htr_json_uri}
- POST /worker/parse {page_id, layout_uri, htr_json_uri} → {parsed_json_uri}

Workers must be stateless; all I/O via blob + DB.

## 15. Logging, Metrics, and Observability

- Structured logs per job with page_id.
- Persist job history in DB.
- Metrics to capture:
  - avg processing time per stage
  - failure rates per stage
  - % rows requiring manual correction
  - confidence distributions

## 16. Deployment (MVP)

- Docker Compose local dev:
  - postgres
  - api (.NET)
  - worker (python)
  - frontend (vite)
  - optional: blob emulator (Azurite) or local filesystem storage

Production (Azure recommended):

- Azure Database for PostgreSQL
- Azure Blob Storage
- App Service / Container Apps for API + worker
- Frontend hosted on static web app or storage

## 17. Security & Data Integrity

- Role-based access
- Audit trail of corrections
- Immutable original images
- Checksums on artifacts

## 18. Acceptance Criteria

### MVP Acceptance

- User can upload a page image.
- System runs preprocess + layout and produces row crops.
- UI shows detected rows; user can manually type/correct fields.
- Data saved to Postgres.
- Export CSV works for a selected document.

### Post-MVP Acceptance

- HTR prefills text for rows.
- Confidence-based review prioritization.
- Reprocess with new model version without losing old outputs.

## 19. Implementation Order (Recommended)

1. Data model + blob storage + ingest.
2. Preprocess + simple layout detection + row crops.
3. Review UI (keyboard-driven).
4. Export.
5. Add HTR.
6. Add parsing/validation rules.
7. Add reprocess/versioning UX.

## 20. Deliverables (What the coding tool should generate)

- .NET API project with controllers/services, Hangfire job orchestration.
- Postgres migrations (EF Core or Flyway).
- Python worker service with endpoints + OpenCV preprocessing scaffold.
- React frontend with:
  - upload
  - page viewer
  - row review panel
  - export screen
- Docker compose for local development.

---

## Appendix A — Field Set Suggestions

Since ledger formats may vary per volume, allow **document templates**:

- Define a schema per document: column names + types + parsing rules.

Template table:

- document_id
- schema_json (columns, expected currency format, etc.)

## Appendix B — Confidence Strategy

Confidence computed from:

- layout confidence
- HTR confidence
- rule validation (totals match, amounts parse cleanly)

Use overall row confidence to prioritize review.
