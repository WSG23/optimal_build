# Production Deployment Guide

This guide covers deploying the Building Compliance Platform to production environments.

## Quick Start

```bash
# 1. Copy and configure production environment
cp .env.production.template .env.production
# Edit .env.production with your values

# 2. Build and deploy locally with Docker Compose
docker compose -f docker-compose.prod.yml up -d

# 3. Or deploy to GCP Cloud Run (via GitHub Actions)
git push origin main  # Triggers staging deployment
```

## Architecture Overview

```
                    ┌─────────────────┐
                    │   Cloud Run     │
                    │   (Frontend)    │
                    │   Nginx + React │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   Cloud Run     │
                    │   (Backend)     │
                    │   FastAPI       │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼───────┐   ┌───────▼───────┐   ┌───────▼───────┐
│  Cloud SQL    │   │  Cloud        │   │  Cloud        │
│  PostgreSQL   │   │  Memorystore  │   │  Storage      │
│  + PostGIS    │   │  (Redis)      │   │  (S3-compat)  │
└───────────────┘   └───────────────┘   └───────────────┘
```

## Prerequisites

- Docker and Docker Compose v2+
- Google Cloud SDK (for GCP deployment)
- PostgreSQL 14+ with PostGIS extension
- Redis 6+ (for rate limiting and caching)
- S3-compatible storage (MinIO, GCS, or AWS S3)

## Configuration

### Required Environment Variables

These MUST be set in production:

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key (32+ chars, random) | `openssl rand -hex 32` |
| `SQLALCHEMY_DATABASE_URI` | PostgreSQL connection string | `postgresql+asyncpg://user:pass@host/db` |
| `BACKEND_ALLOWED_ORIGINS` | CORS allowed origins (comma-separated) | `https://app.example.com` |
| `ENVIRONMENT` | Must be `production` | `production` |

### Optional Configuration

See `.env.production.template` for complete list. Key options:

**Database Pool Settings:**
```bash
DB_POOL_SIZE=10           # Connection pool size (default: 10)
DB_MAX_OVERFLOW=20        # Additional connections allowed (default: 20)
DB_POOL_TIMEOUT=30        # Wait time for connection (seconds)
DB_POOL_RECYCLE=1800      # Recycle connections after (seconds)
```

**Rate Limiting:**
```bash
API_RATE_LIMIT=100/minute     # Default rate limit per IP
RATE_LIMIT_STORAGE_URI=redis://redis:6379/3
```

**Feature Flags:**
```bash
BUILDABLE_USE_POSTGIS=true    # Enable PostGIS for spatial queries
OFFLINE_MODE=false            # Disable external API calls
```

## Deployment Methods

### 1. Docker Compose (Self-Hosted)

For single-server or on-premise deployments:

```bash
# Build and start all services
docker compose -f docker-compose.prod.yml up -d --build

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Scale backend
docker compose -f docker-compose.prod.yml up -d --scale backend=3

# Stop all services
docker compose -f docker-compose.prod.yml down
```

**Health Checks:**
- Backend: `http://localhost:8000/health`
- Frontend: `http://localhost:80/`
- Metrics: `http://localhost:8000/metrics`

### 2. Google Cloud Run (Recommended)

Automated via GitHub Actions (`.github/workflows/deploy.yml`):

**Staging Deployment:**
- Triggers on push to `main` branch
- Deploys to `us-central1` region
- URL: `https://backend-staging-*.run.app`

**Production Deployment:**
- Triggers on GitHub release publish
- Requires manual release creation
- URL: `https://backend-*.run.app`

**Required GitHub Secrets:**
```
GCP_PROJECT_ID          # Your GCP project ID
GCP_SA_KEY              # Service account JSON key
PROD_SECRET_KEY         # Production SECRET_KEY
PROD_DATABASE_URL       # Cloud SQL connection string
PROD_ALLOWED_ORIGINS    # Production CORS origins
```

**Manual Deployment:**
```bash
# Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Build and push
docker build -t gcr.io/YOUR_PROJECT/backend:latest ./backend
docker push gcr.io/YOUR_PROJECT/backend:latest

# Deploy
gcloud run deploy backend \
  --image gcr.io/YOUR_PROJECT/backend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "ENVIRONMENT=production,SECRET_KEY=$SECRET_KEY"
```

### 3. Kubernetes (Advanced)

For Kubernetes deployments, adapt the Docker Compose configuration:

```yaml
# Example deployment (adjust as needed)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    spec:
      containers:
      - name: backend
        image: gcr.io/YOUR_PROJECT/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: secret-key
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
```

## Database Setup

### PostgreSQL with PostGIS

```sql
-- Create database and user
CREATE USER buildable WITH PASSWORD 'secure_password';
CREATE DATABASE building_compliance OWNER buildable;

-- Enable PostGIS
\c building_compliance
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE building_compliance TO buildable;
```

### Migrations

```bash
# Run migrations
cd backend
alembic upgrade head

# Check current version
alembic current

# Rollback one migration
alembic downgrade -1
```

### Cloud SQL Setup (GCP)

```bash
# Create instance
gcloud sql instances create building-compliance \
  --database-version=POSTGRES_14 \
  --tier=db-custom-2-8192 \
  --region=us-central1 \
  --storage-auto-increase

# Enable PostGIS (requires Cloud SQL Admin API)
gcloud sql instances patch building-compliance \
  --database-flags=cloudsql.enable_pg_cron=on

# Create database
gcloud sql databases create building_compliance \
  --instance=building-compliance
```

## Security Considerations

### TLS/HTTPS

- Cloud Run: TLS is automatic
- Docker Compose: Use a reverse proxy (Nginx, Traefik, Caddy)
- Always redirect HTTP to HTTPS in production

### Secrets Management

**Development:** Use `.env` files (never commit to git)

**Production Options:**
- GCP Secret Manager (recommended for Cloud Run)
- AWS Secrets Manager
- HashiCorp Vault
- Kubernetes Secrets

Example with GCP Secret Manager:
```bash
# Create secret
echo -n "your-secret-key" | gcloud secrets create SECRET_KEY --data-file=-

# Use in Cloud Run
gcloud run services update backend \
  --set-secrets="SECRET_KEY=SECRET_KEY:latest"
```

### Network Security

- Configure firewall rules to restrict database access
- Use VPC Service Controls for sensitive workloads
- Enable Cloud SQL Auth Proxy for secure database connections

## Monitoring

### Health Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Application health with database check |
| `GET /metrics` | Prometheus metrics |
| `GET /health/metrics` | Detailed health metrics |

### Prometheus Metrics

The backend exposes Prometheus metrics at `/metrics`:

```
# Example metrics
http_requests_total{endpoint="health",method="GET"}
http_request_duration_seconds{endpoint="buildable",quantile="0.99"}
db_pool_size{pool="default"}
db_pool_overflow{pool="default"}
```

### Logging

Logs are structured JSON for easy parsing:

```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "level": "info",
  "event": "request_completed",
  "path": "/api/v1/screen/buildable",
  "method": "POST",
  "status": 200,
  "duration_ms": 142
}
```

Configure log aggregation with:
- Google Cloud Logging (automatic with Cloud Run)
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Grafana Loki

## Troubleshooting

### Common Issues

**Database connection failed:**
```bash
# Check connectivity
pg_isready -h $POSTGRES_HOST -p 5432

# Check credentials
psql $SQLALCHEMY_DATABASE_URI -c "SELECT 1"
```

**CORS errors:**
```bash
# Verify BACKEND_ALLOWED_ORIGINS includes your frontend URL
curl -H "Origin: https://your-frontend.com" \
  -I https://api.your-domain.com/health
```

**Rate limiting issues:**
```bash
# Check Redis connection
redis-cli -u $RATE_LIMIT_STORAGE_URI ping

# Increase rate limit for testing
API_RATE_LIMIT=1000/minute
```

**Memory issues:**
```bash
# Increase container memory
docker compose -f docker-compose.prod.yml up -d \
  --memory=2g backend
```

### Debug Mode (NOT for production)

```bash
# Enable debug logging temporarily
LOG_LEVEL=DEBUG docker compose -f docker-compose.prod.yml up backend
```

## Backup and Recovery

### Database Backups

```bash
# Manual backup
pg_dump -h $POSTGRES_HOST -U $POSTGRES_USER -Fc $POSTGRES_DB > backup.dump

# Restore
pg_restore -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB backup.dump
```

### Cloud SQL Automated Backups

Enabled by default in Cloud SQL. Configure retention:
```bash
gcloud sql instances patch building-compliance \
  --backup-start-time=02:00 \
  --retained-backups-count=30
```

## Scaling

### Horizontal Scaling

**Cloud Run:**
```bash
gcloud run services update backend \
  --min-instances=2 \
  --max-instances=10 \
  --concurrency=80
```

**Docker Compose:**
```bash
docker compose -f docker-compose.prod.yml up -d --scale backend=5
```

### Database Connection Pooling

Production defaults (configurable via environment):
- `DB_POOL_SIZE=10` - Base connections per worker
- `DB_MAX_OVERFLOW=20` - Additional connections during peaks
- `DB_POOL_PRE_PING=true` - Verify connections before use

For Cloud Run with many instances, consider PgBouncer:
```bash
# Add to docker-compose.prod.yml
pgbouncer:
  image: pgbouncer/pgbouncer:latest
  environment:
    DATABASES_HOST: postgres
    DATABASES_PORT: 5432
    PGBOUNCER_POOL_MODE: transaction
    PGBOUNCER_MAX_CLIENT_CONN: 1000
```

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/deploy.yml`) provides:

1. **Build Stage:** Docker image build with caching
2. **Test Stage:** Run unit and integration tests
3. **Push Stage:** Push to Google Container Registry
4. **Deploy Stage:** Deploy to Cloud Run
5. **Smoke Test:** Verify deployment health

### Rollback

```bash
# Cloud Run - revert to previous revision
gcloud run services update-traffic backend \
  --to-revisions=backend-00001-abc=100

# Docker Compose - use previous image tag
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

## Related Documentation

- [Architecture Overview](./architecture.md)
- [Security Guide](./SECURITY.md)
- [API Documentation](/docs)
- [Contributing Guide](../CONTRIBUTING.md)
