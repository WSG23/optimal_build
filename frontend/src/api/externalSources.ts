import { boolish, coerceString } from './shared'

export type ExternalSourceState = 'live' | 'mock' | 'unavailable'

export interface ExternalSourceMetadata {
  provider: string
  state: ExternalSourceState
  configured: boolean
  synthetic: boolean
  reason?: string | null
}

export function mapExternalSourceMetadata(
  payload: unknown,
): ExternalSourceMetadata | null {
  if (!payload || typeof payload !== 'object') {
    return null
  }

  const source = payload as Record<string, unknown>
  const provider = coerceString(source.provider)
  const rawState = coerceString(source.state)?.toLowerCase()
  if (!provider || !rawState) {
    return null
  }

  const state: ExternalSourceState =
    rawState === 'live' || rawState === 'mock' || rawState === 'unavailable'
      ? rawState
      : 'unavailable'

  return {
    provider,
    state,
    configured: boolish(source.configured),
    synthetic: boolish(source.synthetic),
    reason: coerceString(source.reason) ?? null,
  }
}
