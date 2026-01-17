# Incident Response Playbook

This playbook provides procedures for responding to production incidents in optimal_build.

## Incident Severity Levels

| Severity | Description | Response Time | Examples |
|----------|-------------|---------------|----------|
| **SEV1** | Service completely down | < 15 min | All users unable to access, data loss |
| **SEV2** | Major functionality impaired | < 30 min | Core features broken, high error rate |
| **SEV3** | Minor functionality impaired | < 2 hours | Non-critical feature broken, degraded performance |
| **SEV4** | Cosmetic or minor issue | Next business day | UI glitches, minor bugs |

---

## Incident Response Process

### 1. Detection & Triage (0-5 minutes)

#### Identify the Issue

```bash
# Check service health
curl -sf https://optimal-build.example.com/health | jq

# Check error rates
kubectl logs -l app=optimal-build -n optimal-build --tail=100 | grep -i error

# Check Grafana dashboard
# URL: https://grafana.optimal-build.example.com/d/api-overview
```

#### Assess Severity

Ask these questions:
1. Is the entire service down?
2. How many users are affected?
3. Is data at risk?
4. Is there a security breach?

#### Create Incident Channel

```
Slack: #incident-YYYYMMDD-brief-description
```

### 2. Communication (5-10 minutes)

#### Internal Notification

Post to `#incidents`:
```
:rotating_light: **INCIDENT** - [SEV2] - API Error Rate Spike

**Status:** Investigating
**Impact:** Users experiencing slow response times
**Started:** 2024-01-15 14:30 UTC
**Lead:** @oncall-engineer

Updates in #incident-20240115-api-errors
```

#### External Communication (if needed)

Update status page:
```
**Investigating** - We are investigating reports of slow API response times.
We will provide an update within 30 minutes.
```

### 3. Investigation (10-30 minutes)

#### Gather Data

```bash
# Application logs
kubectl logs -l app=optimal-build -n optimal-build --since=30m | head -500

# Error distribution
kubectl logs -l app=optimal-build -n optimal-build --since=30m | \
  grep -oP 'error.*' | sort | uniq -c | sort -rn

# Recent deployments
kubectl rollout history deployment/optimal-build-backend -n optimal-build

# Recent config changes
git log --oneline --since="1 hour ago"

# Database status
kubectl exec -it <backend-pod> -n optimal-build -- \
  python -c "from app.core.database import engine; print(engine.pool.status())"
```

#### Check Metrics

1. **Error Rate**: Prometheus query
   ```promql
   sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))
   ```

2. **Latency**: Prometheus query
   ```promql
   histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
   ```

3. **Resource Usage**: Prometheus query
   ```promql
   container_memory_usage_bytes{namespace="optimal-build"} / container_spec_memory_limit_bytes
   ```

### 4. Mitigation (30-60 minutes)

#### Common Mitigations

**Scale up resources:**
```bash
kubectl scale deployment/optimal-build-backend --replicas=6 -n optimal-build
```

**Rollback deployment:**
```bash
kubectl rollout undo deployment/optimal-build-backend -n optimal-build
```

**Restart pods:**
```bash
kubectl rollout restart deployment/optimal-build-backend -n optimal-build
```

**Enable maintenance mode:**
```bash
# Update ingress to show maintenance page
kubectl apply -f infra/kubernetes/maintenance-ingress.yaml
```

**Block problematic traffic:**
```bash
# Add rate limiting rule
kubectl apply -f infra/kubernetes/emergency-rate-limit.yaml
```

### 5. Resolution

#### Verify Fix

```bash
# Check health
curl -sf https://optimal-build.example.com/health | jq

# Check error rate is decreasing
# Monitor Grafana for 15 minutes

# Run smoke tests
cd tests/e2e && npx playwright test specs/smoke.spec.ts
```

#### Close Incident

Post to incident channel:
```
:white_check_mark: **INCIDENT RESOLVED**

**Duration:** 45 minutes
**Root Cause:** Database connection pool exhaustion due to slow query
**Fix:** Optimized query and increased pool size
**Follow-up:** [JIRA-123] Add query performance monitoring
```

Update status page:
```
**Resolved** - The issue has been resolved. API response times have returned to normal.
```

---

## Incident Runbooks by Type

### Runbook: Service Unavailable (5xx errors)

**Symptoms:**
- Health check returning 503
- All API calls failing
- Grafana shows 100% error rate

**Investigation:**

```bash
# Check pod status
kubectl get pods -n optimal-build

# Check for OOMKilled
kubectl get pods -n optimal-build -o jsonpath='{.items[*].status.containerStatuses[*].lastState.terminated.reason}' | tr ' ' '\n' | sort | uniq -c

# Check node resources
kubectl top nodes
kubectl describe nodes | grep -A5 "Allocated resources"
```

**Resolution:**

1. If pods are OOMKilled:
   ```bash
   # Increase memory limits
   kubectl set resources deployment/optimal-build-backend -n optimal-build \
     --limits=memory=2Gi
   ```

2. If nodes are exhausted:
   ```bash
   # Scale down non-critical workloads or add nodes
   kubectl scale deployment/monitoring-tools --replicas=0 -n monitoring
   ```

3. If deployment is stuck:
   ```bash
   # Force restart
   kubectl rollout restart deployment/optimal-build-backend -n optimal-build
   ```

---

### Runbook: Database Issues

**Symptoms:**
- Slow queries
- Connection timeouts
- "too many connections" errors

**Investigation:**

```bash
# Check connection count
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "
SELECT count(*), state FROM pg_stat_activity GROUP BY state;
"

# Check for blocking queries
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "
SELECT pid, now() - pg_stat_activity.query_start AS duration, query, state
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';
"

# Check database size
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "
SELECT pg_size_pretty(pg_database_size('$POSTGRES_DB'));
"
```

**Resolution:**

1. Kill long-running queries:
   ```sql
   SELECT pg_terminate_backend(pid) FROM pg_stat_activity
   WHERE duration > interval '10 minutes' AND state != 'idle';
   ```

2. Clear idle connections:
   ```sql
   SELECT pg_terminate_backend(pid) FROM pg_stat_activity
   WHERE state = 'idle' AND query_start < now() - interval '30 minutes';
   ```

3. Add missing indexes:
   ```sql
   -- Check for sequential scans on large tables
   SELECT relname, seq_scan, idx_scan
   FROM pg_stat_user_tables
   WHERE seq_scan > 1000 AND idx_scan < 100;
   ```

---

### Runbook: High Latency

**Symptoms:**
- P95 latency > 500ms
- Users reporting slow page loads
- Grafana latency alerts firing

**Investigation:**

```bash
# Identify slow endpoints
kubectl logs -l app=optimal-build -n optimal-build --since=30m | \
  grep -oP 'endpoint="\K[^"]+' | sort | uniq -c | sort -rn

# Check database query times
kubectl logs -l app=optimal-build -n optimal-build --since=30m | \
  grep slow_query

# Check external API calls
kubectl logs -l app=optimal-build -n optimal-build --since=30m | \
  grep -E 'external_api|timeout'
```

**Resolution:**

1. Scale up if CPU-bound:
   ```bash
   kubectl scale deployment/optimal-build-backend --replicas=6 -n optimal-build
   ```

2. Enable caching:
   ```bash
   kubectl exec -it <backend-pod> -- redis-cli FLUSHDB  # Clear stale cache
   ```

3. Add circuit breaker for slow external APIs:
   ```python
   # Temporarily disable slow external calls
   ```

---

### Runbook: Security Incident

**Symptoms:**
- Unusual traffic patterns
- Failed authentication attempts
- Unauthorized data access

**Immediate Actions:**

1. **Preserve Evidence:**
   ```bash
   # Save logs
   kubectl logs -l app=optimal-build -n optimal-build --since=24h > incident-logs-$(date +%Y%m%d).txt

   # Save audit logs
   PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "
   COPY (SELECT * FROM compliance_audit_logs WHERE created_at > now() - interval '24 hours')
   TO '/tmp/audit-$(date +%Y%m%d).csv' CSV HEADER;
   "
   ```

2. **Block Attacker (if identified):**
   ```bash
   # Add IP to block list
   kubectl apply -f - <<EOF
   apiVersion: networking.k8s.io/v1
   kind: NetworkPolicy
   metadata:
     name: block-attacker
     namespace: optimal-build
   spec:
     podSelector: {}
     ingress:
     - from:
       - ipBlock:
           cidr: 0.0.0.0/0
           except:
           - <attacker-ip>/32
   EOF
   ```

3. **Rotate Credentials:**
   ```bash
   # Rotate API keys
   # Rotate database passwords
   # Rotate JWT secrets
   ```

4. **Notify Security Team:**
   - Email: security@optimal-build.com
   - Slack: #security-incidents

---

## Post-Incident Review

### Blameless Postmortem Template

```markdown
# Incident Postmortem: [Brief Description]

**Date:** YYYY-MM-DD
**Duration:** X hours Y minutes
**Severity:** SEV2
**Lead:** [Name]

## Summary
[2-3 sentence summary of what happened]

## Timeline (UTC)
- 14:30 - Alert fired for high error rate
- 14:35 - On-call engineer acknowledged
- 14:45 - Root cause identified
- 15:00 - Fix deployed
- 15:15 - Incident resolved

## Root Cause
[What actually caused the incident]

## Impact
- X users affected
- Y requests failed
- Z minutes of degraded service

## What Went Well
- Detection was fast
- Communication was clear
- Rollback worked smoothly

## What Went Wrong
- Alert threshold was too high
- Runbook was outdated
- Recovery took longer than expected

## Action Items
| Action | Owner | Due Date |
|--------|-------|----------|
| Add monitoring for X | @engineer | 2024-01-20 |
| Update runbook for Y | @sre | 2024-01-22 |
| Implement circuit breaker | @engineer | 2024-01-25 |

## Lessons Learned
[Key takeaways for the team]
```

---

## Appendix: Emergency Contacts

| Role | Contact | Escalation Path |
|------|---------|-----------------|
| Primary On-Call | PagerDuty | Auto-escalates after 15 min |
| Secondary On-Call | PagerDuty | Auto-escalates after 30 min |
| Engineering Manager | Phone | Manual escalation for SEV1 |
| Security | security@optimal-build.com | All security incidents |
| Legal | legal@optimal-build.com | Data breaches |
