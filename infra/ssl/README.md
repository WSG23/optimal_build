# SSL/TLS Configuration

This directory contains SSL/TLS certificate management configuration for production deployments.

## Certificate Options

### 1. AWS Certificate Manager (Recommended for AWS)

ACM provides free, auto-renewing certificates for use with AWS services.

```bash
# Request a certificate
aws acm request-certificate \
  --domain-name optimal-build.example.com \
  --validation-method DNS \
  --subject-alternative-names "*.optimal-build.example.com"
```

### 2. Let's Encrypt (Self-managed)

Free certificates with 90-day validity. Use certbot for automatic renewal.

```bash
# Install certbot
apt-get install certbot

# Obtain certificate
certbot certonly --standalone \
  -d optimal-build.example.com \
  -d www.optimal-build.example.com

# Auto-renewal is configured automatically
# Check with: systemctl status certbot.timer
```

### 3. Self-Signed (Development Only)

Generate self-signed certificates for local development:

```bash
# Generate private key
openssl genrsa -out server.key 4096

# Generate self-signed certificate
openssl req -new -x509 -sha256 \
  -key server.key \
  -out server.crt \
  -days 365 \
  -subj "/CN=localhost"
```

## Nginx Configuration

See `nginx-ssl.conf` for production-ready Nginx SSL configuration with:
- TLS 1.2+ only
- Strong cipher suites
- HSTS headers
- OCSP stapling

## Kubernetes TLS

For Kubernetes deployments, use cert-manager for automatic certificate management:

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: optimal-build-tls
spec:
  secretName: optimal-build-tls-secret
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
    - optimal-build.example.com
```
