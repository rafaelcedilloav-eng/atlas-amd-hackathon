FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev \
    tesseract-ocr poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements-server.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-server.txt

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

COPY src/ ./src/

EXPOSE 8000

CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
