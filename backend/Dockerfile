# ── Stage 1: Build ────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --target=/install -r requirements.txt

# ── Stage 2: Runtime ──────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages
COPY --from=builder /install /usr/local/lib/python3.12/site-packages/

# Copy application code
COPY . .

# Non-root user for security
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

# Cloud Run expects the PORT environment variable
ENV PORT=8080
EXPOSE $PORT

CMD ["sh", "-c", "python -m uvicorn main:app --host 0.0.0.0 --port $PORT"]
