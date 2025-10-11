function normaliseBaseUrl(value: string | undefined | null): string {
  if (typeof value !== 'string') {
    return '/'
  }
  const trimmed = value.trim()
  return trimmed === '' ? '/' : trimmed
}

const metaEnv =
  typeof import.meta !== 'undefined' && import.meta
    ? (import.meta as ImportMeta).env
    : undefined
const rawApiBaseUrl = metaEnv?.VITE_API_BASE_URL ?? null
const apiBaseUrl = normaliseBaseUrl(rawApiBaseUrl)

function buildUrl(path: string, base: string = apiBaseUrl) {
  const normalised = base.endsWith('/') ? base.slice(0, -1) : base
  if (path.startsWith('/')) {
    return `${normalised}${path}`
  }
  return `${normalised}/${path}`
}

export interface ListingIntegrationAccount {
  id: string
  user_id: string
  provider: string
  status: string
  metadata?: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface PublishResult {
  listing_id: string
  provider_payload: Record<string, unknown>
}

export async function fetchListingAccounts(signal?: AbortSignal) {
  const response = await fetch(buildUrl('/api/v1/integrations/listings/accounts'), {
    signal,
  })
  if (!response.ok) {
    throw new Error('Failed to load listing accounts')
  }
  return (await response.json()) as ListingIntegrationAccount[]
}

export async function connectMockPropertyGuru(code: string) {
  const response = await fetch(
    buildUrl('/api/v1/integrations/listings/propertyguru/connect'),
    {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ code, redirect_uri: 'http://localhost/callback' }),
    },
  )
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || 'Failed to connect PropertyGuru account')
  }
  return (await response.json()) as ListingIntegrationAccount
}

export async function publishMockPropertyGuru(payload: Record<string, unknown>) {
  const response = await fetch(
    buildUrl('/api/v1/integrations/listings/propertyguru/publish'),
    {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(payload),
    },
  )
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || 'Failed to publish listing')
  }
  return (await response.json()) as PublishResult
}

export async function disconnectMockPropertyGuru() {
  const response = await fetch(
    buildUrl('/api/v1/integrations/listings/propertyguru/disconnect'),
    { method: 'POST' },
  )
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || 'Failed to disconnect PropertyGuru account')
  }
  return (await response.json()) as { status: string; provider: string }
}
