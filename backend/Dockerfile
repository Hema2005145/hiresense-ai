# --- Base image ---
FROM python:3.11-slim AS base

# Prevents Python from writing .pyc files and buffers stdout, so logs
# appear immediately in `docker logs` instead of being buffered.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System dependencies required by PyMuPDF, faiss-cpu, and spaCy's
# compiled components.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# --- Dependency layer (cached separately from source code so that
# code-only changes don't trigger a full reinstall of every package) ---
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m spacy download en_core_web_sm

# --- Application source ---
COPY . .

# Non-root user for defense-in-depth — the container runs as an
# unprivileged user rather than root.
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
