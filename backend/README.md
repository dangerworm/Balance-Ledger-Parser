# Ledger HTR Lab Backend

FastAPI backend for the Ledger HTR Lab prototype with preprocessing pipeline and multiple HTR engines.

## Features

- **Multiple HTR Engines**: Dummy, Tesseract, TrOCR, Kraken
- **Preprocessing Pipeline**: Grayscale, contrast stretch, denoise, thresholding, inversion
- **Bounding Box Padding**: Configurable padding for better recognition
- **Performance Metrics**: Elapsed time tracking
- **Dual Crop Output**: Both raw and preprocessed crops returned

## Prerequisites

The Tesseract HTR engine requires Tesseract OCR to be installed on your system:

### Windows
```bash
winget install UB-Mannheim.TesseractOCR
```
Or download the installer from: https://github.com/UB-Mannheim/tesseract/wiki

### macOS
```bash
brew install tesseract
```

### Linux (Ubuntu/Debian)
```bash
sudo apt-get install tesseract-ocr
```

## HTR Engines

### Tesseract (Baseline)
- Uses LSTM OCR engine with PSM 7 (single line mode)
- Expected to perform poorly on cursive handwriting
- Used as a baseline comparator

### TrOCR (Primary)
- Transformer-based OCR from HuggingFace
- Handwritten model variant optimized for historical documents
- CPU-compatible, GPU optional
- Downloads model on first use (~1GB)

### Kraken (HTR-oriented)
- Specialized for historical documents
- Requires a trained model file (.mlmodel)
- Set `KRAKEN_MODEL_PATH` environment variable to use
- Will show clear error if model not configured

## Running locally

### Initial setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate
```

### Starting the server

Option 1 - Using the startup script (recommended):
```bash
# On Windows (Git Bash)
./start_server.sh

# On Windows (CMD)
start_server.bat
```

Option 2 - Direct command (if you prefer not to activate venv):
```bash
.venv/Scripts/uvicorn.exe app.main:app --reload --port 8000
```

Option 3 - With activated venv:
```bash
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

## API Endpoints

### POST /api/htr

Run HTR on a selected region with preprocessing.

**Request:**
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

**Response:**
```json
{
  "image_id": "uuid",
  "engine": "trocr",
  "bbox": { "x": 77, "y": 1022, "w": 2304, "h": 177 },
  "padding": { "pad_x": 10, "pad_y": 5 },
  "preprocess_applied": ["grayscale", "contrast_stretch", "threshold:otsu"],
  "text": "Per transport ...",
  "confidence": 0.61,
  "elapsed_ms": 842,
  "raw_crop_url": "/api/crop/{id}?crop_type=raw",
  "preprocessed_crop_url": "/api/crop/{id}?crop_type=preprocessed"
}
```
