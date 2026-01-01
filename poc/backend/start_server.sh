#!/bin/bash
# Start the backend server without activating venv
cd "$(dirname "$0")"
.venv/Scripts/uvicorn.exe app.main:app --reload --port 8000
