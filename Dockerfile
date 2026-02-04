FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY tests/ ./tests/
COPY README.md ./
COPY .env.example ./

EXPOSE 8000

# Railway sets PORT; default to 8000 locally.
CMD sh -c "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"
