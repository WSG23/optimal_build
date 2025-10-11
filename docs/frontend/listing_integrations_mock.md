# Listing Integration (Mock) Guide

Phase 1C validates the listing integration workflow without live credentials.
This guide explains how to exercise the mock PropertyGuru and EdgeProp flows end-to-end.

## Overview

- **Accounts** are stored in `listing_integration_accounts` with mock tokens.
- **Listings** are tracked in `listing_publications` but publish calls simply echo
  payloads via `PropertyGuruClient`.
- Once real credentials arrive we will replace the stubbed HTTP calls inside
  `backend/app/services/integrations/propertyguru.py`.

## Backend Endpoints

| Method | Path | Purpose |
| ------ | ---- | ------- |
| `GET` | `/api/v1/integrations/listings/accounts` | List linked accounts for the current user |
| `POST` | `/api/v1/integrations/listings/{provider}/connect` | Store mock tokens (`provider` = `propertyguru` or `edgeprop`) |
| `POST` | `/api/v1/integrations/listings/{provider}/publish` | Echo publish payloads (stores nothing yet) |
| `POST` | `/api/v1/integrations/listings/{provider}/disconnect` | Revoke mock tokens |

All endpoints expect a Bearer token so they can associate accounts with a user.

## Frontend Flow

Visit **`/agents/integrations`** in the staging UI:

1. **Link each provider** – enter any string as the authorization code for
   PropertyGuru or EdgeProp.
2. **Publish mock listing** – supply a property ID (e.g. from the advisory page)
   and an external listing id; the call returns the same value.
3. **Disconnect** – removes the mock account for that provider.

The page calls the mock API client in `frontend/src/api/listings.ts`; swapping in
real endpoints later only requires changing that client.

## Next Steps

- When production credentials arrive, implement the real OAuth/token refresh
  calls inside `PropertyGuruClient` and enable token encryption.
- Extend this pattern to EdgeProp and Zoho CRM connectors.
