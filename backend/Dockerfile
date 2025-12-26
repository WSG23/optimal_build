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
COPY _compat /app/backend/_compat
COPY jobs /app/backend/jobs
COPY scripts /app/backend/scripts
COPY prefect /app/backend/prefect
COPY migrations /app/backend/migrations

USER appuser

ENV PORT=8080 \
    WEB_CONCURRENCY=2 \
    GUNICORN_TIMEOUT=60

EXPOSE 8080

# Security: Restrict forwarded IPs to trusted proxy networks only
# This prevents IP spoofing attacks from untrusted sources
CMD gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:${PORT} \
    --workers ${WEB_CONCURRENCY} \
    --timeout ${GUNICORN_TIMEOUT} \
    --graceful-timeout 30 \
    --keep-alive 5 \
    --access-logfile - \
    --error-logfile - \
    --forwarded-allow-ips="10.0.0.0/8,172.16.0.0/12,192.168.0.0/16" \
    --limit-request-line 8190 \
    --limit-request-fields 100 \
    --limit-request-field_size 8190
