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

export interface ListingProviderOption {
  provider: string
  label: string
  description?: string
  brandColor?: string
}

export interface PublishResult {
  listing_id: string
  provider_payload: Record<string, unknown>
}

export async function fetchListingAccounts(signal?: AbortSignal) {
  const response = await fetch(
    buildUrl('/api/v1/integrations/listings/accounts'),
    {
      signal,
    },
  )
  if (!response.ok) {
    throw new Error('Failed to load listing accounts')
  }
  return (await response.json()) as ListingIntegrationAccount[]
}

export async function fetchListingProviders(
  signal?: AbortSignal,
): Promise<ListingProviderOption[]> {
  const response = await fetch(
    buildUrl('/api/v1/integrations/listings/providers'),
    {
      signal,
    },
  )
  if (!response.ok) {
    throw new Error('Failed to load listing providers')
  }
  const payload = (await response.json()) as Array<Record<string, unknown>>
  if (!Array.isArray(payload)) {
    return []
  }
  return payload.map((entry) => ({
    provider: String(entry.provider ?? ''),
    label: String(entry.label ?? entry.provider ?? ''),
    description:
      entry.description != null ? String(entry.description) : undefined,
    brandColor:
      entry.brand_color != null ? String(entry.brand_color) : undefined,
  }))
}

export async function connectListingAccount(
  provider: string,
  code: string,
  redirectUri?: string,
) {
  const computedRedirectUri =
    redirectUri ?? (typeof window !== 'undefined' ? window.location.origin : '')
  const response = await fetch(
    buildUrl(`/api/v1/integrations/listings/${provider}/connect`),
    {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        code,
        redirect_uri: computedRedirectUri,
      }),
    },
  )
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || `Failed to connect ${provider} account`)
  }
  return (await response.json()) as ListingIntegrationAccount
}

export async function publishListing(
  provider: string,
  payload: Record<string, unknown>,
) {
  const response = await fetch(
    buildUrl(`/api/v1/integrations/listings/${provider}/publish`),
    {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(payload),
    },
  )
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || `Failed to publish ${provider} listing`)
  }
  return (await response.json()) as PublishResult
}

export async function disconnectListingAccount(provider: string) {
  const response = await fetch(
    buildUrl(`/api/v1/integrations/listings/${provider}/disconnect`),
    { method: 'POST' },
  )
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || `Failed to disconnect ${provider} account`)
  }
  return (await response.json()) as { status: string; provider: string }
}
