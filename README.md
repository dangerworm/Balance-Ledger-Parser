# Ledger HTR Lab

Prototype web application for quickly testing handwritten text recognition (HTR) on ledger scans. The tool lets you upload an image, select a region, run an HTR engine, and view recognized text alongside a cropped preview.

## Structure

- `backend/` — FastAPI service with in-memory storage and pluggable HTR engines.
- `frontend/` — React + Vite single-page app for upload, selection, and result display.

## Running the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Running the frontend

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_URL` to point to the backend if it differs from `http://localhost:8000`.
