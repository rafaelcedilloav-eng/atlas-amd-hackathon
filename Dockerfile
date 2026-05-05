# ███ ATLAS v3.0 - Dockerfile - AACDU v3.1 Certified
# Multi-stage build para seguridad y minimización de superficie de ataque

# Stage 1: Build Stage
FROM python:3.11-slim-bookworm AS builder

LABEL maintainer="atlas-team@corp.com"
LABEL security.scan="trivy-scan-on-build"
LABEL version="3.0.0"

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY requirements.txt requirements-prod.txt ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --compile -r requirements-prod.txt

# Stage 2: Runtime Stage
FROM python:3.11-slim-bookworm

RUN groupadd -r atlas && useradd -r -g atlas -d /app atlas

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* && \
    apt-get clean

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src \
    APP_ENV=production

WORKDIR /app
RUN chown -R atlas:atlas /app

COPY --chown=atlas:atlas src/ ./src/
COPY --chown=atlas:atlas entrypoint.sh ./
RUN chmod +x entrypoint.sh

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)"

USER atlas

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "--config", "src/config/gunicorn_conf.py", "src.api.main:app"]
