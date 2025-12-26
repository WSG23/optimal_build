# Cloud Run Deployment (Backend + Frontend)

This repo is set up to deploy:
- `backend/` as a FastAPI service on Cloud Run.
- `frontend/` as a static Vite build served by nginx on Cloud Run.

No custom domain is required to start; Cloud Run provides `*.run.app` URLs.

## Prerequisites

- `gcloud` installed and authenticated (`gcloud auth login`)
- A GCP project with billing enabled
- Docker installed locally
- An Artifact Registry repository (Docker) created in your chosen region

Enable APIs:

```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com
```

## One-time setup

Create an Artifact Registry repo (example):

```bash
gcloud artifacts repositories create <GAR_REPOSITORY> \
  --repository-format=docker \
  --location=<REGION>
```

Configure Docker auth for Artifact Registry:

```bash
gcloud auth configure-docker <REGION>-docker.pkg.dev
```

## Deploy

Use `infra/gcp/cloudrun/deploy.sh` to build/push images and deploy both services:

```bash
export PROJECT_ID="<your-gcp-project>"
export REGION="us-central1"
export GAR_REPOSITORY="optimal-build"
export API_SERVICE="optimal-build-api"
export WEB_SERVICE="optimal-build-web"

./infra/gcp/cloudrun/deploy.sh
```

After the first deploy, set `BACKEND_ALLOWED_ORIGINS` on the backend service to the
Cloud Run URL of the frontend service (for example `https://<web>.run.app`).

## Database + migrations (recommended)

If you use Cloud SQL, set `CLOUDSQL_INSTANCE` so Cloud Run can connect:

```bash
export CLOUDSQL_INSTANCE="project:region:instance"
```

Create a migration job and run it:

```bash
export MIGRATE_JOB="optimal-build-migrate"
./infra/gcp/cloudrun/deploy.sh migrate
```

The migration command is:
`python -m backend.migrations alembic upgrade head`

## Secrets/config

Cloud Run services should be configured with required env vars/secrets (at minimum `SECRET_KEY`).
This repo intentionally does not bake secrets into images or scripts.

Recommended pattern:
- Store secrets in Secret Manager
- Attach them to the Cloud Run service as environment variables
- Keep `ENVIRONMENT=production` in production

## P2: Production infrastructure

See `infra/gcp/cloudrun/P2_PROVISIONING.md` for Cloud SQL, Secret Manager, and Cloud Storage setup.

## CI/CD (GitHub Actions)

`.github/workflows/deploy-cloudrun.yml` supports:
- auto-deploy to `staging` on `main`
- manual deploy to `staging` or `production` via workflow dispatch

Create GitHub Environments named `staging` and `production` and configure:

Environment variables (`vars`):
- `GCP_PROJECT_ID`
- `GCP_REGION`
- `GAR_REPOSITORY`
- `CLOUD_RUN_API_SERVICE`
- `CLOUD_RUN_WEB_SERVICE`
- `CLOUD_RUN_MIGRATE_JOB` (optional; leave blank to skip migrations)

Environment secrets:
- `GCP_WIF_PROVIDER`
- `GCP_WIF_SERVICE_ACCOUNT`
