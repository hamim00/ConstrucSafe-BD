# Copilot / AI Agent Instructions for ConstructSafe-BD 🔧

This file contains concise, actionable guidance for AI coding agents working in this repo. Focus on *discoverable* patterns and files so you can be productive immediately.

## Big picture (what this service does) 💡
- FastAPI backend that maps detected construction-safety violations to Bangladesh laws and penalties.
- Primary responsibilities:
  - Serve law data endpoints (fully implemented)
  - Provide an image/analysis API (currently a Phase 1 stub)
  - Generate PDF reports (stubbed)
- Key entry points: `backend/main.py` (app setup), `backend/routers/*` (HTTP surface), `backend/services/law_matcher.py` (law lookup), `backend/data/laws.json` (knowledge base).

## Important files & directories 🔭
- `backend/main.py` — app + middleware + router registration (`/api/v1` prefix)
- `backend/config.py` — pydantic-based `Settings` and env parsing (see field validators for list parsing)
- `backend/routers/` — `laws.py` (implemented), `analyze.py` (stub), `reports.py` (stub)
- `backend/services/law_matcher.py` — loads `backend/data/laws.json` and provides lookup helpers
- `backend/data/laws.json` — canonical + micro violations, authorities, penalty profiles, source catalog
- `README.md` — quickstart, endpoints, and Docker commands (use as authoritative dev/run commands)

## Run / Dev workflows (concrete commands) ▶️
- Local dev (see `README.md`):
  - python -m venv .venv; activate; pip install -r requirements.txt
  - copy `.env.example` to `.env` and set `GEMINI_API_KEY`
  - run server: `uvicorn backend.main:app --reload --port 8000`
  - health: `GET /health`; interactive docs: `GET /docs`
- Docker:
  - `docker build -t construcsafe-bd-backend .`
  - `docker run -p 8000:8000 --env-file .env construcsafe-bd-backend`

## Config / environment to watch ⚙️
- `.env` keys used by code: `GEMINI_API_KEY`, `GEMINI_MODEL` (defaults to `gemini-1.5-flash`)
- `Settings` includes:
  - `MAX_IMAGE_SIZE_MB`, `ALLOWED_EXTENSIONS` (string or comma-separated env supported), `CORS_ALLOW_ORIGINS`
  - Validators parse comma-separated strings into lists — preserve that pattern when adding new settings

## Data conventions & constraints (very important) 📚
- `backend/data/laws.json` structure expected by `LawMatcher`:
  - Top-level keys: `metadata`, `source_catalog`, `authorities`, `penalty_profiles`, `canonical_violations`, `micro_violations`
  - Violation objects include: `violation_id`, `display_name_en`, `category`, `severity`, `visual_indicators`, `legal_references`, `penalty_profiles`, `enforcement` (example: `HELMET_MISSING`)
- Do NOT rename top-level keys or existing `violation_id` values — LawMatcher builds indexes by `violation_id` and `authority_id`.
- When adding entries: update `metadata.version` and `metadata.last_updated`.
- Note: some text fields may contain legacy Bengali encodings; preserve original text and encoding.

## API & implementation patterns 🧭
- Router registration: all routers use `app.include_router(..., prefix="/api/v1")` in `backend/main.py`.
- Tags: use `APIRouter(tags=["..."])` to categorize endpoints (see `Laws`, `Analysis`, `Reports`).
- Error handling: routers use `fastapi.HTTPException` (see `backend/routers/laws.py` 404 examples).
- Service instantiation: `LawMatcher()` is instantiated at module import in `backend/routers/laws.py`. Keep service constructors lightweight (data loading occurs at import time).
- When implementing `analyze` endpoint:
  - Follow the README API signature: `POST /api/v1/analyze` with multipart `file` param
  - Validate file size against `settings.MAX_IMAGE_SIZE_MB` and extension against `settings.ALLOWED_EXTENSIONS`
  - Return JSON shaped similarly to `violations` results described in README and `laws` endpoints

## Small but important conventions ✅
- Keep changes discoverable and minimal: when adding routes, add tests and update `README.md` docs.
- Use clear `violation_id` strings (UPPER_SNAKE_CASE) to match existing entries (example: `HELMET_MISSING`).
- For new features that require model/LLM access, read `backend/config.py` and use `GEMINI_API_KEY`/`GEMINI_MODEL` env pattern.

## Example tasks an AI agent can do right away 🛠️
- Implement `analyze` router: accept image, validate, call a placeholder analysis function, and return a stubbed JSON response with `violation_id` keys present in `data/laws.json`.
- Add unit tests for `LawMatcher` lookups (e.g., `get_all_violation_types()`, `get_violation_details("HELMET_MISSING")`).
- Add basic PDF generation for `reports` or wire up an existing library and return `application/pdf` per README.

---
If anything in these instructions is unclear or you'd like more examples (e.g., sample expected response bodies or a starter test file), tell me which section to expand and I will iterate. 👩‍💻