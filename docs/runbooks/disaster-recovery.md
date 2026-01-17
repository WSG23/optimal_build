# Disaster Recovery Plan

## Overview

This document outlines the disaster recovery (DR) procedures for optimal_build. It covers backup strategies, recovery procedures, and business continuity planning.

## Recovery Objectives

| Metric | Target | Description |
|--------|--------|-------------|
| **RTO** (Recovery Time Objective) | 4 hours | Maximum acceptable downtime |
| **RPO** (Recovery Point Objective) | 1 hour | Maximum acceptable data loss |
| **MTTR** (Mean Time To Recovery) | 2 hours | Expected average recovery time |

## Disaster Categories

### Category 1: Application Failure
- **Severity**: Low
- **Examples**: Pod crash, memory leak, application bug
- **Recovery Time**: < 15 minutes
- **Procedure**: Kubernetes auto-healing, rollback deployment

### Category 2: Database Failure
- **Severity**: Medium
- **Examples**: Database corruption, replication lag, connection exhaustion
- **Recovery Time**: < 1 hour
- **Procedure**: Failover to replica, point-in-time recovery

### Category 3: Infrastructure Failure
- **Severity**: High
- **Examples**: AZ outage, Kubernetes cluster failure, network partition
- **Recovery Time**: < 2 hours
- **Procedure**: Multi-AZ failover, cluster rebuild

### Category 4: Complete Site Failure
- **Severity**: Critical
- **Examples**: Region outage, catastrophic data center failure
- **Recovery Time**: < 4 hours
- **Procedure**: Cross-region recovery, backup restoration

---

## Backup Strategy

### Database Backups

**Automated Daily Backups**
- **Schedule**: 02:00 UTC daily
- **Retention**: 30 days
- **Location**: S3 bucket `optimal-build-backups-{env}`
- **Encryption**: AES-256 at rest, TLS in transit

```bash
# Verify backup exists
aws s3 ls s3://optimal-build-backups-prod/postgres/ --recursive | tail -5

# Check backup integrity
aws s3 cp s3://optimal-build-backups-prod/postgres/backup-2024-01-15.sql.gz - | gzip -t
```

**Point-in-Time Recovery (PITR)**
- **WAL Archiving**: Enabled, 5-minute intervals
- **Retention**: 7 days of WAL files
- **Recovery granularity**: Any point within retention window

### Application State

**Kubernetes Resources**
```bash
# Export all resources
kubectl get all,configmaps,secrets,ingress,pvc -n optimal-build -o yaml > cluster-backup.yaml

# Store in S3
aws s3 cp cluster-backup.yaml s3://optimal-build-backups-prod/kubernetes/
```

**Persistent Volumes**
- EBS snapshots: Daily, 7-day retention
- Cross-region replication: Enabled for critical volumes

### Configuration Backups

| Item | Location | Frequency |
|------|----------|-----------|
| Helm values | Git repository | On change |
| Secrets | AWS Secrets Manager | On change |
| TLS certificates | AWS Certificate Manager | Auto-renewed |
| DNS records | Route53 (versioned) | On change |

---

## Recovery Procedures

### Procedure 1: Application Rollback

**When to use**: Application bug, failed deployment, performance regression

```bash
# 1. Check current deployment status
kubectl rollout status deployment/optimal-build-backend -n optimal-build

# 2. View rollout history
kubectl rollout history deployment/optimal-build-backend -n optimal-build

# 3. Rollback to previous version
kubectl rollout undo deployment/optimal-build-backend -n optimal-build

# 4. Verify rollback
kubectl get pods -n optimal-build -w

# 5. Check application health
curl -f https://app.optimalbuild.com/health
```

**Rollback to specific version**:
```bash
# Find revision number
kubectl rollout history deployment/optimal-build-backend -n optimal-build

# Rollback to specific revision
kubectl rollout undo deployment/optimal-build-backend -n optimal-build --to-revision=3
```

### Procedure 2: Database Point-in-Time Recovery

**When to use**: Data corruption, accidental deletion, need to recover to specific point

```bash
# 1. Stop application to prevent new writes
kubectl scale deployment/optimal-build-backend -n optimal-build --replicas=0

# 2. Create new database from backup
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier optimal-build-prod \
  --target-db-instance-identifier optimal-build-prod-recovery \
  --restore-time "2024-01-15T14:30:00Z"

# 3. Wait for instance to be available
aws rds wait db-instance-available \
  --db-instance-identifier optimal-build-prod-recovery

# 4. Verify data integrity
psql -h optimal-build-prod-recovery.xxx.rds.amazonaws.com -U admin -d optimal_build \
  -c "SELECT COUNT(*) FROM projects; SELECT MAX(updated_at) FROM projects;"

# 5. Update application configuration to use new database
kubectl set env deployment/optimal-build-backend \
  DATABASE_HOST=optimal-build-prod-recovery.xxx.rds.amazonaws.com \
  -n optimal-build

# 6. Scale application back up
kubectl scale deployment/optimal-build-backend -n optimal-build --replicas=3

# 7. Verify application health
curl -f https://app.optimalbuild.com/health
```

### Procedure 3: Full Database Restore from Backup

**When to use**: Complete database loss, cross-region recovery

```bash
# 1. Download latest backup
aws s3 cp s3://optimal-build-backups-prod/postgres/backup-latest.sql.gz ./

# 2. Decompress
gunzip backup-latest.sql.gz

# 3. Create new database
createdb -h $DB_HOST -U admin optimal_build_restored

# 4. Restore backup
psql -h $DB_HOST -U admin -d optimal_build_restored < backup-latest.sql

# 5. Verify restoration
psql -h $DB_HOST -U admin -d optimal_build_restored \
  -c "SELECT COUNT(*) FROM projects; SELECT COUNT(*) FROM users;"

# 6. Rename databases (during maintenance window)
psql -h $DB_HOST -U admin -c "
  ALTER DATABASE optimal_build RENAME TO optimal_build_old;
  ALTER DATABASE optimal_build_restored RENAME TO optimal_build;
"

# 7. Restart application
kubectl rollout restart deployment/optimal-build-backend -n optimal-build
```

### Procedure 4: Kubernetes Cluster Recovery

**When to use**: Cluster corruption, control plane failure

```bash
# 1. Create new EKS cluster
eksctl create cluster -f infra/eks/cluster-config.yaml

# 2. Restore secrets from AWS Secrets Manager
kubectl create secret generic app-secrets \
  --from-literal=DATABASE_URL=$(aws secretsmanager get-secret-value \
    --secret-id optimal-build/prod/database --query SecretString --output text) \
  -n optimal-build

# 3. Deploy application
helm install optimal-build infra/helm/optimal-build \
  -f infra/helm/values-prod.yaml \
  -n optimal-build

# 4. Restore database connection
kubectl set env deployment/optimal-build-backend \
  DATABASE_HOST=$RDS_ENDPOINT \
  -n optimal-build

# 5. Update DNS to point to new cluster
aws route53 change-resource-record-sets \
  --hosted-zone-id $HOSTED_ZONE_ID \
  --change-batch file://dns-update.json

# 6. Verify application
curl -f https://app.optimalbuild.com/health
```

### Procedure 5: Cross-Region Failover

**When to use**: Complete region failure

```bash
# 1. Promote read replica in DR region
aws rds promote-read-replica \
  --db-instance-identifier optimal-build-dr-replica

# 2. Wait for promotion
aws rds wait db-instance-available \
  --db-instance-identifier optimal-build-dr-replica

# 3. Deploy application to DR region
kubectl config use-context optimal-build-dr-cluster

helm install optimal-build infra/helm/optimal-build \
  -f infra/helm/values-dr.yaml \
  -n optimal-build

# 4. Update global DNS
aws route53 change-resource-record-sets \
  --hosted-zone-id $HOSTED_ZONE_ID \
  --change-batch file://dns-failover.json

# 5. Notify stakeholders
./scripts/notify-incident.sh "Region failover completed"
```

---

## Communication Plan

### Escalation Matrix

| Severity | Response Time | Notification | Escalation |
|----------|---------------|--------------|------------|
| P1 - Critical | 15 min | All teams, executives | CTO within 30 min |
| P2 - High | 30 min | Engineering, DevOps | Engineering Manager within 1 hour |
| P3 - Medium | 2 hours | On-call engineer | Team lead within 4 hours |
| P4 - Low | 24 hours | Ticket created | Normal sprint process |

### Status Page Updates

1. **Investigating**: Initial acknowledgment
2. **Identified**: Root cause determined
3. **Monitoring**: Fix deployed, watching for stability
4. **Resolved**: Full service restored

### Communication Templates

**Initial Notification**:
```
Subject: [INCIDENT] Optimal Build Service Disruption

We are currently investigating reports of service degradation.
- Start time: [TIME]
- Impact: [DESCRIPTION]
- Status: Investigating

Updates will be provided every 30 minutes.
```

**Resolution**:
```
Subject: [RESOLVED] Optimal Build Service Restored

The service disruption has been resolved.
- Duration: [DURATION]
- Root cause: [BRIEF DESCRIPTION]
- Impact: [AFFECTED USERS/FEATURES]

A full post-incident review will be conducted.
```

---

## Testing Schedule

### Monthly Tests

| Test | Description | Duration |
|------|-------------|----------|
| Backup Verification | Restore random backup to test environment | 2 hours |
| Failover Drill | Simulate primary database failure | 1 hour |
| Runbook Review | Verify procedures are current | 30 min |

### Quarterly Tests

| Test | Description | Duration |
|------|-------------|----------|
| Full DR Drill | End-to-end disaster recovery simulation | 4 hours |
| Cross-Region Failover | Test DR region activation | 2 hours |
| Chaos Engineering | Inject failures in production (controlled) | 2 hours |

### Annual Tests

| Test | Description | Duration |
|------|-------------|----------|
| Tabletop Exercise | Walk through major disaster scenarios | 4 hours |
| DR Plan Review | Full plan update and approval | 8 hours |
| Third-Party Audit | External DR capability assessment | 2 days |

---

## Recovery Checklist

### Pre-Recovery

- [ ] Assess incident severity and category
- [ ] Notify stakeholders per escalation matrix
- [ ] Update status page
- [ ] Gather incident team
- [ ] Review relevant runbook

### During Recovery

- [ ] Follow documented procedure
- [ ] Log all actions with timestamps
- [ ] Communicate progress every 30 minutes
- [ ] Verify each recovery step before proceeding

### Post-Recovery

- [ ] Verify all services operational
- [ ] Run smoke tests
- [ ] Update status page to resolved
- [ ] Schedule post-incident review
- [ ] Document lessons learned
- [ ] Update runbooks if needed

---

## Appendix

### Key Contacts

| Role | Contact | Backup |
|------|---------|--------|
| On-Call Engineer | PagerDuty rotation | Slack #on-call |
| Database Admin | [Name] | [Backup Name] |
| Infrastructure Lead | [Name] | [Backup Name] |
| CTO | [Name] | CEO |

### External Contacts

| Service | Support | Account ID |
|---------|---------|------------|
| AWS Support | Premium support | [Account ID] |
| Sentry | support@sentry.io | [Org ID] |
| PagerDuty | [Support URL] | [Account] |

### Recovery Scripts Location

```
infra/backup/backup.sh        # Database backup script
infra/backup/restore.sh       # Database restore script
scripts/dr/failover.sh        # Automated failover script
scripts/dr/health-check.sh    # Post-recovery verification
```

---

**Document Version**: 1.0
**Last Updated**: 2025-01-17
**Next Review**: 2025-04-17
**Owner**: DevOps Team
