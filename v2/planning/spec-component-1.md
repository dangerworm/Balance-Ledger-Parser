# Component 1: Image Ingestion & Pre‑Processing Service

## Purpose

Convert raw scanned ledger images into clean, geometrically normalised, single‑page images suitable for downstream AI processing and human review.

## Inputs

* High‑resolution scanned images (typically two‑page spreads)
* Minimal external metadata (file name, source archive, scan batch)

## Outputs

For each input image:

* One or more **normalised page images** (PNG/TIFF)
* Associated **page metadata records**

## Processing Steps

1. **Image Intake**

   * Assign a unique image ID
   * Store original image immutably

2. **Page Boundary Detection**

   * Detect outer page edges using OpenCV or equivalent
   * Identify book gutter / centre fold

3. **Margin Expansion**

   * Expand detected page boundary by a configurable margin
   * Ensure no ink or ruling is clipped

4. **Geometric Normalisation**

   * Deskew using detected page edges (not handwriting angle)
   * Apply perspective correction to fit page into a true rectangle

5. **De-warping**

   * Optional de‑warping near gutter (future enhancement)

6. **Page Splitting**

   * Split two‑page spreads into left and right pages
   * Assign page side (left/right)
   * Assign "bridge" facts
     * spread_layout_type (e.g. paired account / mixed / etc.)
     * links: left_page_id, right_page_id
     * allows “paired blocks” across pages (debit table ↔ credit table)

7. **Derivative Storage**

   * Store:

     * Original image
     * Cropped raw page
     * Normalised page image

## Metadata Captured

* Original image ID
* Page ID
* Left/right designation
* Detected page number (if present; optional OCR assist)
* Book / volume identifier (if known)
* 'Bridge' data (if applicable)
* Processing version

## Error Handling and Degradation

The service must always emit something (even if marked low-confidence), never
silently drop input. For example, the component could return a warning or error
state if any of the below are true, but would still store data to the database
with a status of `NeedsReview`:

* page boundary detection fails
* only one page is detected in a spread
* gutter detection is ambiguous

## Non‑Goals

* No semantic interpretation
* No text extraction
