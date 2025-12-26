FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN adduser --disabled-password --gecos "" appuser


FROM base AS builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-prod.txt /app/requirements-prod.txt

RUN python -m pip install --upgrade pip \
    && python -m pip install --prefix=/install -r /app/requirements-prod.txt


FROM base AS runtime

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

COPY app /app/app
COPY migrations /app/backend/migrations

USER appuser

ENV PORT=8080 \
    WEB_CONCURRENCY=2 \
    GUNICORN_TIMEOUT=60

EXPOSE 8080

CMD gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:${PORT} \
    --workers ${WEB_CONCURRENCY} \
    --timeout ${GUNICORN_TIMEOUT} \
    --graceful-timeout 30 \
    --keep-alive 5 \
    --access-logfile - \
    --error-logfile - \
    --forwarded-allow-ips="*"
