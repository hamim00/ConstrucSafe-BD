# ConstrucSafe BD (Backend)

FastAPI backend for construction safety violation detection + Bangladesh law mapping.

## Quickstart (Local)

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# edit .env and set GEMINI_API_KEY

uvicorn backend.main:app --reload --port 8000
```

Health check: `GET /health`

Interactive docs: `GET /docs`

## API

- `POST /api/v1/analyze` (multipart upload `file`) -> violations (optionally with laws)
- `GET /api/v1/laws/violations` -> supported violation types
- `GET /api/v1/laws/violations/{violation_id}` -> law mapping details
- `GET /api/v1/laws/authorities/{authority_id}` -> enforcement authority info
- `POST /api/v1/reports/generate` -> PDF report (returns application/pdf)

## Docker

```bash
docker build -t construcsafe-bd-backend .
docker run -p 8000:8000 --env-file .env construcsafe-bd-backend
```
