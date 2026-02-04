FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/

# Railway provides PORT automatically. Fallback to 8000 locally.
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
