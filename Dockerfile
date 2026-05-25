# ── Builder Stage ──────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir --user hatchling

# ── Runtime Stage ──────────────────────────────────────────
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# System deps: Playwright browsers + PostgreSQL client
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libdbus-1-3 libexpat1 libxcb1 \
    libxkbcommon0 libx11-6 libxcomposite1 libxdamage1 \
    libxext6 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 \
    libcairo2 libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium
RUN playwright install chromium && playwright install-deps chromium

# Copy application code
COPY ecommerce_ops/ ./ecommerce_ops/
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY dashboard/dist ./dashboard/dist

# Create non-root user
RUN addgroup --system app && adduser --system --ingroup app app
RUN chown -R app:app /app
USER app

EXPOSE 8000

CMD ["uvicorn", "ecommerce_ops.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
