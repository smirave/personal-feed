# Personal Feed AI Generator

This project now runs as a FastAPI-based web application with a polished frontend dashboard.

## Run locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
3. Open http://localhost:8000/

## API

- `GET /api/prompts`
- `POST /api/generate`
- `GET /health`

Prompts are discovered automatically from the `prompts/` directory.
