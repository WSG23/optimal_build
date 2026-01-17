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

### Recommended Rotation Periods

| Secret Type | Rotation Period |
|-------------|-----------------|
| Database passwords | 30 days |
| API keys | 90 days |
| JWT secrets | 180 days |
| SSL certificates | Before expiry |
