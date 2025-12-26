# P2: Production Infrastructure (GCP)

This phase turns the Cloud Run deploy scaffolding into a production-grade setup:

- Cloud SQL (Postgres + PostGIS) for data
- Secret Manager for secrets (no `.env` in production)
- Cloud Storage for object storage
- Optional: Memorystore (Redis) + VPC connector
- Monitoring/alerts and operational guardrails

## 1) Cloud SQL (Postgres + PostGIS)

Create the instance and database/user:

```bash
export PROJECT_ID="..."
export REGION="us-central1"
export CLOUDSQL_INSTANCE="optimal-build-db"
export CLOUDSQL_DB="building_compliance"
export CLOUDSQL_USER="app"

./infra/gcp/cloudrun/provision_cloudsql.sh
```

After creation, connect and enable PostGIS:

```bash
gcloud sql connect "${CLOUDSQL_INSTANCE}" --user=postgres --project="${PROJECT_ID}"
```

Then in `psql`:

```sql
\\c building_compliance
CREATE EXTENSION IF NOT EXISTS postgis;
```

### Cloud Run connection

Recommended: use Cloud Run's Cloud SQL attachment (`--add-cloudsql-instances`) plus a **Unix socket** URI:

`SQLALCHEMY_DATABASE_URI=postgresql+asyncpg://USER:PASSWORD@/DBNAME?host=/cloudsql/PROJECT:REGION:INSTANCE`

Example:

`postgresql+asyncpg://app:...@/building_compliance?host=/cloudsql/myproj:us-central1:optimal-build-db`

## 2) Secret Manager

Create secrets (examples):

```bash
export PROJECT_ID="..."
./infra/gcp/cloudrun/provision_secrets.sh create SECRET_KEY
./infra/gcp/cloudrun/provision_secrets.sh create SQLALCHEMY_DATABASE_URI
```

Attach secrets to Cloud Run (service-level):

```bash
gcloud run services update <api-service> \
  --region="${REGION}" \
  --set-secrets="SECRET_KEY=SECRET_KEY:latest,SQLALCHEMY_DATABASE_URI=SQLALCHEMY_DATABASE_URI:latest" \
  --set-env-vars="ENVIRONMENT=production,BACKEND_ALLOWED_ORIGINS=[\"https://<web>.run.app\"]"
```

## 3) Cloud Storage buckets

Create buckets for imports/exports/documents:

```bash
export PROJECT_ID="..."
export REGION="us-central1"
export BUCKET_PREFIX="optimal-build"

./infra/gcp/cloudrun/provision_storage.sh
```

Then configure the app to use GCS (recommended approach):
- Prefer using native GCS clients in code, OR
- Use an S3-compatible gateway only if you must keep S3 semantics

## 4) Optional: Redis (Memorystore) + VPC connector

Only needed if you require Redis in production (rate limiting storage, queues, caching).

High-level steps:
- Create a Serverless VPC Access connector in the same region.
- Create a Memorystore Redis instance.
- Configure Cloud Run to use the VPC connector and set `REDIS_URL` to the private IP.

## 5) Monitoring + alerts

Minimum recommended alerts:
- API 5xx rate > threshold (e.g. 1% for 5m)
- P95 latency > threshold
- Cloud SQL CPU/storage/connection saturation
- Error logs spike (optionally via Sentry)
