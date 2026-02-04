# ConstrucSafe BD (Backend)

FastAPI backend for construction safety violation detection + Bangladesh law mapping.

## Quickstart (Local)

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# edit .env and set OPENAI_API_KEY

uvicorn backend.main:app --reload --port 8000
```

Health check: `GET /health`

Interactive docs: `GET /docs`

## API

- `POST /api/v1/analyze` (multipart upload `file`) -> violations (optionally with laws)
  - Includes `flagged_for_review` for sensitive, uncertain detections (e.g., child labor). These are **not confirmed** and require human verification; any attached laws/penalties are conditional.
- `GET /api/v1/laws/violations` -> supported violation types
- `GET /api/v1/laws/violations/{violation_id}` -> law mapping details
- `GET /api/v1/laws/authorities/{authority_id}` -> enforcement authority info
- `POST /api/v1/reports/generate` -> PDF report (returns application/pdf)

## Docker

```bash
docker build -t construcsafe-bd-backend .
docker run -p 8000:8000 --env-file .env construcsafe-bd-backend
```

## Phase 4 (Testing + Deployment)

This repo includes:
- **Pytest test suite** under `tests/` (no real OpenAI calls; VisionAnalyzer is mocked)
- **Dockerfile** (Railway-ready)
- **GitHub Actions CI** workflow (`.github/workflows/ci.yml`)

### Run tests locally
```bash
pip install -r requirements.txt
pytest -q
```

### Run locally (dev)
```bash
uvicorn backend.main:app --reload --port 8000
```

### Docker (same as Railway)
```bash
docker build -t constructsafe-bd .
docker run -p 8000:8000 --env-file .env constructsafe-bd
```

### Railway deployment (recommended for your frontend integration)
Railway is a good choice here because:
- you already have a clean Dockerfile
- you can set **OPENAI_API_KEY** as a secret environment variable
- your Streamlit frontend can call a stable public API URL

**Steps:**
1. Push this repo to GitHub.
2. Railway → **New Project** → **Deploy from GitHub Repo**
3. Railway → Variables:
   - `OPENAI_API_KEY` = your key
   - (optional) `OPENAI_MODEL_FAST`, `OPENAI_MODEL_ACCURATE`
   - (optional) `CORS_ALLOW_ORIGINS` = your Streamlit domain
4. Deploy. Railway will detect the `Dockerfile` and run:
   `uvicorn backend.main:app --host 0.0.0.0 --port $PORT` (Railway sets `$PORT`)
   If Railway does not inject `$PORT` into the Docker CMD, set Railway "Start Command" to:
   `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

**After deploy**, verify:
- `GET /health`
- `GET /api/v1/laws/violations`
- `POST /api/v1/analyze`

### Streamlit frontend integration
In Streamlit, store your Railway base URL:
- `BACKEND_URL=https://<your-railway-service>.up.railway.app`
Then call endpoints like:
- `{BACKEND_URL}/api/v1/analyze`
- `{BACKEND_URL}/api/v1/laws/violations`
