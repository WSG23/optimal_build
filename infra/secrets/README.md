# Secrets Management

This directory contains configuration and utilities for managing secrets in production environments.

## Supported Secret Managers

1. **AWS Secrets Manager** (Recommended for AWS deployments)
2. **HashiCorp Vault** (For multi-cloud or on-premise)
3. **Environment Variables** (Development only)

## Setup Instructions

### AWS Secrets Manager

1. Create secrets in AWS Secrets Manager:
   ```bash
   aws secretsmanager create-secret \
     --name optimal-build/production/database \
     --secret-string '{"username":"postgres","password":"your-secure-password","host":"your-rds-endpoint"}'

   aws secretsmanager create-secret \
     --name optimal-build/production/app \
     --secret-string '{"secret_key":"your-256-bit-secret","jwt_secret":"your-jwt-secret"}'
   ```

2. Grant IAM permissions to your application:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "secretsmanager:GetSecretValue"
         ],
         "Resource": "arn:aws:secretsmanager:*:*:secret:optimal-build/*"
       }
     ]
   }
   ```

3. Set environment variable:
   ```bash
   export SECRETS_MANAGER=aws
   export AWS_REGION=ap-southeast-1
   ```

### HashiCorp Vault

1. Enable the KV secrets engine:
   ```bash
   vault secrets enable -path=optimal-build kv-v2
   ```

2. Store secrets:
   ```bash
   vault kv put optimal-build/production/database \
     username=postgres \
     password=your-secure-password \
     host=your-db-host

   vault kv put optimal-build/production/app \
     secret_key=your-256-bit-secret \
     jwt_secret=your-jwt-secret
   ```

3. Set environment variables:
   ```bash
   export SECRETS_MANAGER=vault
   export VAULT_ADDR=https://vault.example.com
   export VAULT_TOKEN=your-vault-token
   ```

## Secret Rotation

Both AWS Secrets Manager and Vault support automatic secret rotation. Configure rotation policies according to your security requirements.

### External Provider Service Accounts

Use dedicated company-controlled service accounts for external data providers.
Do not use a personal employee account for production integrations.

For Singapore OneMap:

- Register a dedicated OneMap account, for example
  `capture-onemap@yourcompany.com`.
- Store `ONEMAP_EMAIL` and `ONEMAP_PASSWORD` in the production secret manager.
- Let the backend mint and cache OneMap access tokens. OneMap tokens are
  short-lived and should not be treated as permanent deployment secrets.
- Keep `ONEMAP_ACCESS_TOKEN` for local debugging or emergency override only.
- Never expose OneMap credentials or tokens to frontend bundles, browser
  responses, analytics, or logs.
- Rotate the OneMap password when operator access changes, after suspected
  exposure, and on the regular external-provider rotation schedule.

### Recommended Rotation Periods

| Secret Type | Rotation Period |
|-------------|-----------------|
| Database passwords | 30 days |
| API keys | 90 days |
| External provider service-account passwords | 90 days |
| JWT secrets | 180 days |
| SSL certificates | Before expiry |
