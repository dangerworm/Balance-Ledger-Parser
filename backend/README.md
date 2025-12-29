# Ledger HTR Lab Backend

FastAPI backend for the Ledger HTR Lab prototype. Endpoints are defined in `app/main.py` and rely on in-memory storage only.

## Running locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
