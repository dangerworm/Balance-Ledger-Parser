# Hope & Co Ledger Digitisation System

This document defines a complete, modular, end‑to‑end system for digitising 18th‑century ledger books (specifically the Hope & Co ledgers, c.1770).

The system is explicitly designed to:

* Handle **multiple radically different page layouts**
* Preserve **forensic traceability** from extracted data back to original pixels
* Combine **AI‑assisted extraction** with **human‑in‑the‑loop review**
* Be built, tested, and validated **incrementally**, component by component
* Avoid over‑commitment to any single OCR/AI technology

Each section below is written as a **standalone technical specification** suitable for hand‑off to an individual development team.

## Incremental Delivery Strategy

### Recommended Build Order

1. Image ingestion + normalisation
2. Page explorer UI
3. Block segmentation
4. Block review UI
5. Block transcription
6. Validation engine
7. Cross‑page logic

Each component should be testable in isolation before integration.

#### Checkpoints

##### Step 3

On completion of step 3, the first end-to-end page breakup should be possible.
At this point we can check the pages -> blocks workflow.

##### Step 5

On completion of step 5, we should be able to fully transcribe a page with evidence.

## System‑Level Principles (Applies to All Components)

These principles are non‑negotiable and should be enforced across all tooling.

### Traceability

#### Artefacts

Every artefact produced by the system MUST be traceable back to:

* Original scanned image
* Normalised page image
* Block image (if applicable)
* Prompt version
* Model version
* Processing timestamp

No derived data may exist without this lineage.

#### Data Storage & Provenance Model

All artefacts, relationships, and decisions are persisted with full auditability.

##### Core Tables (Conceptual)

* OriginalImages
* Pages
* Blocks
* BlockRelationships
* Transcriptions
* ValidationResults
* HumanOverrides
* ProcessingRuns

###### Provenance Guarantees

Every row must include:

* Unique row ID
* Correlation ID
  * Each API hit should generate a correlation ID
  * This ID should be stored in all records created from that action
* Date created
* IsSuperseded flag (essentially a soft delete flag)
* Source IDs
* User ID (which user caused the write)

Whre an AI service was used:

* Prompt version
* Model version
* Timestamp

At time of planning, I can't see a reason why any row should ever be overwritten.

* Limit UPDATE calls to IsSuperseded columns only
* Otherwise allow only INSERT and SELECT

### Determinism Where Possible

* Identical inputs + identical configuration MUST produce identical outputs
* Idempotency should be enforced via hashing and caching

### Verbatim First, Interpretation Second

All extracted textual data must preserve:

* Verbatim transcription (exact as‑seen text)
* Parsed / normalised interpretation (optional, secondary)

The system must never discard verbatim evidence.

### Human Authority

The system proposes. Humans dispose.

* Human corrections override AI output and become authoritative.
* Edits create additional records that take precendence over the original
  while retaining identical back-link references.

## Future Work

### Variants Over Time

As AI abilities improve each component can be modified to use updated models.

This implies:

* Artefacts may have variants over time.
* All downstream artefacts must reference which normalisation they used.

Eventually it is expected that the explorer UI will pick up on this and
tell the user that reprocessing is available.

## Final Note

This system is not attempting to "solve" 18th‑century accounting.

It is building a **power tool** that allows historians and accountants to work faster, more accurately, and with full evidentiary confidence.

That constraint is what keeps the system tractable — and valuable.
