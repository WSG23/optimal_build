# Production Deployment Runbook

This runbook provides step-by-step instructions for deploying optimal_build to production.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Deployment Process](#deployment-process)
3. [Post-Deployment Verification](#post-deployment-verification)
4. [Rollback Procedure](#rollback-procedure)
5. [Common Issues](#common-issues)

---

## Pre-Deployment Checklist

### Code Quality

- [ ] All CI/CD checks passing
- [ ] Code review approved
- [ ] No critical security vulnerabilities
- [ ] Database migrations reviewed

### Infrastructure

- [ ] AWS/Cloud credentials valid
- [ ] Secrets updated in Secrets Manager
- [ ] SSL certificates valid (check expiry)
- [ ] Database backup completed

### Communication

- [ ] Deployment window communicated to stakeholders
- [ ] On-call engineer identified
- [ ] Rollback plan documented

---

## Deployment Process

### Step 1: Create Database Backup

```bash
# Manual backup before deployment
PGPASSWORD=$POSTGRES_PASSWORD pg_dump \
  -h $POSTGRES_HOST \
  -U $POSTGRES_USER \
  -d $POSTGRES_DB \
  --format=custom \
  -f backup_$(date +%Y%m%d_%H%M%S).dump

# Or use the backup script
./infra/backup/backup.sh custom --upload-s3
```

### Step 2: Run Database Migrations

```bash
# Check pending migrations
cd backend
alembic history --verbose

# Run migrations
alembic upgrade head

# Verify migration
alembic current
```

### Step 3: Deploy Backend

#### Using Kubernetes/Helm

```bash
# Update Helm values
helm upgrade optimal-build ./infra/helm/optimal-build \
  --namespace optimal-build \
  --values ./infra/helm/optimal-build/values-production.yaml \
  --set backend.image.tag=$NEW_VERSION \
  --wait \
  --timeout 10m

# Watch rollout
kubectl rollout status deployment/optimal-build-backend -n optimal-build
```

#### Using Docker Compose (Non-K8s)

```bash
# Pull new images
docker compose pull

# Deploy with zero-downtime
docker compose up -d --no-deps --scale backend=3 backend
docker compose up -d --no-deps frontend
```

### Step 4: Deploy Frontend

```bash
# Helm
helm upgrade optimal-build ./infra/helm/optimal-build \
  --namespace optimal-build \
  --set frontend.image.tag=$NEW_VERSION \
  --wait

# Verify
kubectl rollout status deployment/optimal-build-frontend -n optimal-build
```

### Step 5: Verify Deployment

```bash
# Check pod status
kubectl get pods -n optimal-build

# Check logs
kubectl logs -l app=optimal-build,component=backend -n optimal-build --tail=50

# Test health endpoint
curl -sf https://optimal-build.example.com/health | jq
```

---

## Post-Deployment Verification

### Automated Checks

```bash
# Run smoke tests
cd tests/e2e
npx playwright test specs/smoke.spec.ts

# Check API
curl -sf https://optimal-build.example.com/api/v1/test | jq
```

### Manual Verification

1. **Login Test**
   - Navigate to https://optimal-build.example.com
   - Login with test account
   - Verify dashboard loads

2. **Core Feature Test**
   - Submit a buildable screening request
   - Verify results are returned
   - Check response time < 2s

3. **Monitoring Check**
   - Open Grafana dashboard
   - Verify metrics are flowing
   - Check for error spikes

### Verification Checklist

- [ ] Health endpoint returns 200
- [ ] Login flow works
- [ ] Core API endpoints respond
- [ ] No new errors in Sentry
- [ ] No error spikes in Grafana
- [ ] SSL certificate valid
- [ ] Response times within SLO

---

## Rollback Procedure

### When to Rollback

- Health check failing for > 5 minutes
- Error rate > 5%
- P95 latency > 2s
- Critical functionality broken

### Rollback Steps

#### 1. Rollback Application

```bash
# Kubernetes - rollback to previous revision
kubectl rollout undo deployment/optimal-build-backend -n optimal-build
kubectl rollout undo deployment/optimal-build-frontend -n optimal-build

# Or rollback to specific revision
kubectl rollout undo deployment/optimal-build-backend -n optimal-build --to-revision=3

# Verify rollback
kubectl rollout status deployment/optimal-build-backend -n optimal-build
```

#### 2. Rollback Database (if needed)

```bash
# Check current migration
cd backend
alembic current

# Rollback one migration
alembic downgrade -1

# Or rollback to specific revision
alembic downgrade <revision_id>
```

#### 3. Restore Database from Backup (emergency)

```bash
# Download backup from S3
aws s3 cp s3://optimal-build-backups/backups/postgresql/daily/latest.dump ./

# Restore
./infra/backup/restore.sh ./latest.dump
```

### Post-Rollback

1. Notify stakeholders
2. Create incident report
3. Investigate root cause
4. Schedule fix and re-deployment

---

## Common Issues

### Issue: Pods Not Starting

**Symptoms:**
- Pods stuck in `Pending` or `CrashLoopBackOff`

**Diagnosis:**
```bash
kubectl describe pod <pod-name> -n optimal-build
kubectl logs <pod-name> -n optimal-build --previous
```

**Common Causes:**
- Invalid secrets
- Resource limits too low
- Image pull failure

**Resolution:**
```bash
# Check secrets
kubectl get secrets -n optimal-build
kubectl describe secret optimal-build-postgres -n optimal-build

# Check resources
kubectl top pods -n optimal-build
```

### Issue: Database Connection Failures

**Symptoms:**
- Health check returns "degraded"
- Logs show connection errors

**Diagnosis:**
```bash
# Test connection from pod
kubectl exec -it <backend-pod> -n optimal-build -- \
  pg_isready -h $POSTGRES_HOST -U $POSTGRES_USER

# Check RDS status (AWS)
aws rds describe-db-instances --db-instance-identifier optimal-build-prod
```

**Resolution:**
- Verify security groups allow traffic
- Check database credentials in secrets
- Verify database is running

### Issue: High Latency

**Symptoms:**
- P95 latency > 500ms
- Grafana shows slow queries

**Diagnosis:**
```bash
# Check slow queries in logs
kubectl logs -l component=backend -n optimal-build | grep "slow_query"

# Check database connections
kubectl exec -it <backend-pod> -- python -c "
from app.core.database import engine
print(engine.pool.status())
"
```

**Resolution:**
- Check for N+1 queries
- Add database indexes
- Scale up pods
- Check for resource exhaustion

### Issue: SSL Certificate Errors

**Symptoms:**
- Browser shows certificate warning
- curl returns SSL error

**Diagnosis:**
```bash
# Check certificate expiry
echo | openssl s_client -servername optimal-build.example.com \
  -connect optimal-build.example.com:443 2>/dev/null | \
  openssl x509 -noout -dates
```

**Resolution:**
```bash
# Renew with cert-manager
kubectl delete certificate optimal-build-tls -n optimal-build
# Wait for automatic renewal

# Or renew manually with certbot
certbot renew
```

---

## Emergency Contacts

| Role | Name | Contact |
|------|------|---------|
| On-Call Engineer | TBD | PagerDuty |
| Database Admin | TBD | Slack #db-oncall |
| Security | TBD | security@optimal-build.com |
| Product Owner | TBD | Slack #product |

---

## Deployment History

| Date | Version | Deployer | Notes |
|------|---------|----------|-------|
| YYYY-MM-DD | 1.0.0 | Name | Initial production deployment |

---

## Appendix: Useful Commands

```bash
# Get all resources
kubectl get all -n optimal-build

# Port forward for debugging
kubectl port-forward svc/optimal-build-backend 8000:80 -n optimal-build

# Get pod logs with follow
kubectl logs -f -l app=optimal-build -n optimal-build

# Execute shell in pod
kubectl exec -it <pod-name> -n optimal-build -- /bin/sh

# Get recent events
kubectl get events -n optimal-build --sort-by='.lastTimestamp' | tail -20

# Check HPA status
kubectl get hpa -n optimal-build

# Force pod restart
kubectl rollout restart deployment/optimal-build-backend -n optimal-build
```
