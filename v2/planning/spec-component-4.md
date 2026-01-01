# Component 4: Block‑Level Transcription Service ("Transcribe Bot")

## Purpose

Extract structured textual and numeric data from individual blocks.

## Inputs

* Block image
* Block type
* Expected output schema

## Outputs

* Structured JSON data
* Confidence indicators
* Evidence references

## Primary Extraction Engine

* LLM‑vision‑based transcription with strict schema enforcement

## Secondary / Fallback Engines (Optional)

* OCR/HTR engines for numeric columns or targeted re‑reads

## Schemas

* Schemas are built using fields (see below)
* Versioned schemas are stored in a database
* Schemas should be able to be versioned independently of prompts

### Fields

Fields are a specific concept.

* They should have their own unique ID
* Each version should have its own configuration
* They may be deprecated but never deleted
* Schemas are built by attaching versioned fields
  * A new schema is required if a field version is changed

## Output Requirements

For each extracted field:

* `verbatim_value`
* `parsed_value` (if applicable)
* `confidence`
* `evidence` (block ID + coordinates)

## Supported Data Types

* Names (no canonicalisation at this stage)
* Dates (verbatim + parsed)
* Amounts (string + numeric + currency)
* Ledger annotations (e.g. Ditto, carry marks)

## Re‑Processing

* Individual blocks may be re‑run with different prompts or models
* Cached by (block hash + prompt version + model version)
