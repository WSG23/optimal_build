/**
 * Behavioral telemetry client (PR1 of data-collection upgrade).
 *
 * Buffers events in-memory and flushes them to /api/v1/events/batch on a
 * 5-second cadence, on visibility-change to hidden (best-effort beacon), and
 * on demand via `flushTelemetry()`. Persists an anonymous_id + session_id in
 * localStorage / sessionStorage so pre-auth users are still distinguishable.
 *
 * Failure is silent — telemetry must never break the product.
 */

import { ensureIdentityHeaders } from '../../api/identity'
import { buildUrl } from '../../api/shared'

const STORAGE_KEYS = {
  anonymousId: 'ob.telemetry.anonymousId',
  sessionId: 'ob.telemetry.sessionId',
} as const

const MAX_QUEUE = 200
const FLUSH_INTERVAL_MS = 5_000

export interface TrackEventInput {
  eventType: string
  eventName: string
  targetType?: string
  targetId?: string
  payload?: Record<string, unknown>
  path?: string
}

interface QueuedEvent {
  event_type: string
  event_name: string
  target_type?: string
  target_id?: string
  payload?: Record<string, unknown>
  path?: string
  referrer?: string
  anonymous_id: string
  session_id: string
  client_event_id: string
  occurred_at: string
}

function safeRandomUUID(): string {
  if (
    typeof globalThis !== 'undefined' &&
    typeof globalThis.crypto !== 'undefined' &&
    typeof globalThis.crypto.randomUUID === 'function'
  ) {
    return globalThis.crypto.randomUUID()
  }
  // Cheap fallback — not cryptographic, but unique enough for client IDs.
  return `id-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
}

function readOrCreate(key: string, store: Storage | null): string {
  if (store === null) return safeRandomUUID()
  const existing = store.getItem(key)
  if (existing && existing.length > 0) return existing
  const fresh = safeRandomUUID()
  try {
    store.setItem(key, fresh)
  } catch {
    /* storage may be disabled — fall back to ephemeral id */
  }
  return fresh
}

function getStores(): {
  localStore: Storage | null
  sessionStore: Storage | null
} {
  try {
    return {
      localStore: typeof localStorage !== 'undefined' ? localStorage : null,
      sessionStore:
        typeof sessionStorage !== 'undefined' ? sessionStorage : null,
    }
  } catch {
    return { localStore: null, sessionStore: null }
  }
}

const { localStore, sessionStore } = getStores()
const anonymousId = readOrCreate(STORAGE_KEYS.anonymousId, localStore)
const sessionId = readOrCreate(STORAGE_KEYS.sessionId, sessionStore)

const queue: QueuedEvent[] = []
let timer: ReturnType<typeof setTimeout> | null = null
let flushing = false

function endpoint(): string {
  return buildUrl('/api/v1/events/batch')
}

function scheduleFlush(): void {
  if (timer !== null) return
  timer = setTimeout(() => {
    timer = null
    void flushTelemetry()
  }, FLUSH_INTERVAL_MS)
}

export function track(input: TrackEventInput): void {
  if (queue.length >= MAX_QUEUE) {
    // Drop oldest rather than block the UI.
    queue.shift()
  }
  queue.push({
    event_type: input.eventType,
    event_name: input.eventName,
    target_type: input.targetType,
    target_id: input.targetId,
    payload: input.payload,
    path:
      input.path ??
      (typeof location !== 'undefined' ? location.pathname : undefined),
    referrer: typeof document !== 'undefined' ? document.referrer : undefined,
    anonymous_id: anonymousId,
    session_id: sessionId,
    client_event_id: safeRandomUUID(),
    occurred_at: new Date().toISOString(),
  })
  scheduleFlush()
}

export async function flushTelemetry(): Promise<void> {
  if (flushing || queue.length === 0) return
  flushing = true
  const batch = queue.splice(0, queue.length)
  try {
    const headers = new Headers({ 'Content-Type': 'application/json' })
    ensureIdentityHeaders(headers)
    await fetch(endpoint(), {
      method: 'POST',
      headers,
      body: JSON.stringify({ events: batch }),
      keepalive: true,
    })
  } catch {
    // Best-effort — re-queue at the head so we don't lose user activity.
    queue.unshift(...batch)
  } finally {
    flushing = false
  }
}

if (typeof document !== 'undefined') {
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') {
      void flushTelemetry()
    }
  })
}

if (typeof window !== 'undefined') {
  window.addEventListener('pagehide', () => {
    void flushTelemetry()
  })
}

export const telemetryIdentifiers = {
  anonymousId,
  sessionId,
}
