# Web Application Firewall (WAF) Configuration

## Overview

This directory contains WAF configurations for protecting optimal_build from common web attacks.

## Supported WAF Options

### 1. AWS WAF (Recommended for AWS deployments)

**File**: `aws-waf-config.yaml`

**Features**:
- AWS Managed Rules (SQL injection, XSS, known bad inputs)
- Bot control
- Rate limiting (global and per-endpoint)
- Geo-blocking capability
- Custom rules for sensitive paths
- CloudWatch integration

**Deployment**:
```bash
# Using CloudFormation
aws cloudformation deploy \
  --template-file aws-waf-config.yaml \
  --stack-name optimal-build-waf-prod \
  --parameter-overrides Environment=prod RateLimitPerIP=2000

# Using Terraform (alternative)
terraform apply -var="environment=prod"
```

**Cost**: ~$5/month base + $1/million requests

### 2. Cloudflare WAF (Recommended for multi-cloud)

**Configuration via Cloudflare Dashboard or API**:

```bash
# Create WAF ruleset via API
curl -X POST "https://api.cloudflare.com/client/v4/zones/{zone_id}/rulesets" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{
    "name": "optimal-build-waf",
    "kind": "zone",
    "phase": "http_request_firewall_managed",
    "rules": [
      {
        "action": "execute",
        "expression": "true",
        "action_parameters": {
          "id": "efb7b8c949ac4650a09736fc376e9aee"
        }
      }
    ]
  }'
```

**Recommended Cloudflare settings**:
- Enable OWASP Core Ruleset
- Enable Cloudflare Managed Ruleset
- Set Security Level: High
- Enable Bot Fight Mode
- Rate Limiting: 100 requests/10 seconds per IP

### 3. ModSecurity (Self-hosted)

For Kubernetes ingress or standalone nginx:

```yaml
# Add to nginx ingress configmap
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-modsecurity-config
data:
  modsecurity.conf: |
    SecRuleEngine On
    SecRequestBodyAccess On
    SecRule REQUEST_HEADERS:Content-Type "text/xml" \
      "id:'200000',phase:1,t:none,t:lowercase,pass,nolog,ctl:requestBodyProcessor=XML"
    SecRequestBodyLimit 13107200
    SecRequestBodyNoFilesLimit 131072
    SecResponseBodyAccess Off
    SecDebugLogLevel 0
    SecAuditEngine RelevantOnly
    SecAuditLogRelevantStatus "^(?:5|4(?!04))"
    SecAuditLogParts ABIJDEFHZ
    SecAuditLogType Serial
    SecAuditLog /var/log/modsec_audit.log

    # Include OWASP CRS
    Include /etc/nginx/modsecurity/crs-setup.conf
    Include /etc/nginx/modsecurity/rules/*.conf
```

## Protection Layers

### Layer 1: Network Level
- DDoS protection (AWS Shield / Cloudflare)
- IP reputation filtering
- Geo-blocking (if applicable)

### Layer 2: Application Level (WAF)
- SQL injection prevention
- XSS prevention
- CSRF protection
- File upload validation
- Request size limits

### Layer 3: Application Code
- Input validation (Pydantic)
- Output encoding
- Rate limiting (app middleware)
- Authentication/Authorization

## Recommended Rules

### Must-Have Rules

| Rule | Purpose | Action |
|------|---------|--------|
| SQL Injection | Prevent database attacks | Block |
| XSS | Prevent script injection | Block |
| Path Traversal | Prevent file access | Block |
| Command Injection | Prevent OS command execution | Block |
| Rate Limiting | Prevent brute force/DDoS | Block (429) |

### Recommended Rules

| Rule | Purpose | Action |
|------|---------|--------|
| Bot Detection | Block malicious bots | Block/Challenge |
| User-Agent Validation | Block known attack tools | Block |
| Geo-blocking | Block high-risk regions | Block (if applicable) |
| Size Limits | Prevent large payload attacks | Block |

### Custom Rules for optimal_build

```yaml
# Block common attack paths
- pattern: "/(wp-admin|phpmyadmin|.env|.git)"
  action: block

# Stricter limits on auth endpoints
- path: "/api/v1/auth/*"
  rate_limit: 10/minute

# Protect export endpoints (expensive operations)
- path: "/api/v1/*/export"
  rate_limit: 5/minute

# Block requests without valid Accept header
- condition: "missing(request.headers['Accept'])"
  action: block
```

## Monitoring & Alerts

### Key Metrics to Monitor

```yaml
alerts:
  - name: HighBlockedRequestRate
    condition: blocked_requests > 1000/hour
    action: notify_security

  - name: RateLimitTriggered
    condition: rate_limited_requests > 100/5min
    action: investigate_ip

  - name: SQLInjectionAttempt
    condition: sqli_blocked > 0
    action: notify_security

  - name: BotAttack
    condition: bot_blocked > 500/hour
    action: review_bot_rules
```

### Dashboard Setup

1. **AWS WAF**: CloudWatch Dashboard (auto-created by template)
2. **Cloudflare**: Analytics → Security → WAF
3. **ModSecurity**: ELK Stack or Grafana with log parsing

## Testing WAF Rules

### Safe Testing Commands

```bash
# Test SQL injection detection (should be blocked)
curl -X GET "https://app.optimalbuild.com/api/v1/projects?id=1'%20OR%201=1--"

# Test XSS detection (should be blocked)
curl -X POST "https://app.optimalbuild.com/api/v1/comments" \
  -d '{"content": "<script>alert(1)</script>"}'

# Test rate limiting (should be blocked after threshold)
for i in {1..100}; do
  curl -s -o /dev/null -w "%{http_code}\n" "https://app.optimalbuild.com/api/v1/health"
done

# Test path traversal (should be blocked)
curl "https://app.optimalbuild.com/../../../etc/passwd"
```

### Load Testing (Ensure WAF doesn't block legitimate traffic)

```bash
# Use k6 to verify WAF doesn't cause false positives
k6 run tests/load/k6/baseline.js --env TARGET=https://app.optimalbuild.com
```

## Troubleshooting

### False Positives

1. **Check WAF logs** for rule ID that blocked request
2. **Add exception** for specific rule/path combination
3. **Test** to ensure legitimate traffic passes
4. **Document** the exception and reason

### Common Issues

| Issue | Solution |
|-------|----------|
| Large file uploads blocked | Increase body size limit for `/api/v1/files/upload` |
| API requests blocked | Whitelist API client user agents |
| Legitimate bots blocked | Add to bot allowlist (Googlebot, etc.) |
| Webhook requests blocked | Whitelist webhook source IPs |

## Compliance Considerations

- **PCI DSS**: WAF required for cardholder data environments
- **SOC 2**: WAF supports security controls (CC6.6)
- **HIPAA**: WAF helps protect PHI (if applicable)

## Maintenance

### Weekly
- Review blocked request logs
- Check for false positives
- Update IP blocklist

### Monthly
- Review WAF rule effectiveness
- Update managed rule versions
- Performance impact assessment

### Quarterly
- Full WAF rule audit
- Penetration testing with WAF enabled
- Cost optimization review

---

## Quick Reference

### AWS WAF Commands

```bash
# List Web ACLs
aws wafv2 list-web-acls --scope REGIONAL

# Get sampled requests
aws wafv2 get-sampled-requests \
  --web-acl-arn $WAF_ARN \
  --rule-metric-name RateLimitPerIP \
  --scope REGIONAL \
  --time-window StartTime=2024-01-01T00:00:00Z,EndTime=2024-01-02T00:00:00Z \
  --max-items 100

# Update IP set
aws wafv2 update-ip-set \
  --name optimal-build-blocked-ips-prod \
  --scope REGIONAL \
  --id $IP_SET_ID \
  --addresses "1.2.3.4/32" "5.6.7.8/32" \
  --lock-token $LOCK_TOKEN
```

### Cloudflare Commands

```bash
# List WAF rules
curl -X GET "https://api.cloudflare.com/client/v4/zones/{zone_id}/firewall/rules" \
  -H "Authorization: Bearer $CF_API_TOKEN"

# Add IP to blocklist
curl -X POST "https://api.cloudflare.com/client/v4/zones/{zone_id}/firewall/access_rules/rules" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -d '{"mode":"block","configuration":{"target":"ip","value":"1.2.3.4"},"notes":"Malicious actor"}'
```
