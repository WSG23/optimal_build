/**
 * Decision provenance helpers (PR2 of data-collection upgrade).
 *
 * Wrap any UI that renders >1 option in a choice set: call `logChoiceSet`
 * when the alternatives mount, then `resolveChoiceSet` when the user picks
 * one or dismisses the set. The two calls are independently safe — failure
 * in either is silent, telemetry must never break the product.
 */

import { config } from '../../config'
import { ensureIdentityHeaders } from '../../api/identity'

function safeRandomUUID(): string {
  if (
    typeof globalThis !== 'undefined' &&
    typeof globalThis.crypto !== 'undefined' &&
    typeof globalThis.crypto.randomUUID === 'function'
  ) {
    return globalThis.crypto.randomUUID()
  }
  return `cs-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
}

export interface AlternativeInput {
  rank: number
  label?: string
  payload?: Record<string, unknown>
  score?: number
}

export interface LogChoiceSetInput {
  decisionType: string
  contextEntityType?: string
  contextEntityId?: string
  alternatives: AlternativeInput[]
  anonymousId?: string
  sessionId?: string
}

export interface ChoiceSetHandle {
  choiceSetId: string
  presentedAt: number
  resolve: (resolution: ResolveChoiceSetInput) => Promise<void>
}

export interface ResolveChoiceSetInput {
  chosenRank?: number
  dismissedReason?: string
  rationale?: string
}

function endpointFor(path: string): string {
  return `${config.apiBaseUrl.replace(/\/$/, '')}/api/v1/decisions${path}`
}

async function postJson(url: string, body: unknown): Promise<void> {
  try {
    const headers = new Headers({ 'Content-Type': 'application/json' })
    ensureIdentityHeaders(headers)
    await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
      keepalive: true,
    })
  } catch {
    /* swallow — telemetry is best-effort */
  }
}

/**
 * Log a choice set the moment it is presented. Returns a handle whose
 * `resolve` method records which option the user picked (or that they
 * dismissed the set without choosing).
 */
export function logChoiceSet(input: LogChoiceSetInput): ChoiceSetHandle {
  const choiceSetId = safeRandomUUID()
  const presentedAt = Date.now()
  const presentedAtIso = new Date(presentedAt).toISOString()

  void postJson(endpointFor('/choice-sets'), {
    choice_set_id: choiceSetId,
    decision_type: input.decisionType,
    context_entity_type: input.contextEntityType,
    context_entity_id: input.contextEntityId,
    presented_at: presentedAtIso,
    anonymous_id: input.anonymousId,
    session_id: input.sessionId,
    alternatives: input.alternatives.map((alt) => ({
      alternative_rank: alt.rank,
      alternative_label: alt.label,
      alternative_payload: alt.payload,
      score: alt.score,
    })),
  })

  return {
    choiceSetId,
    presentedAt,
    resolve: async (resolution: ResolveChoiceSetInput) => {
      const chosenAt = Date.now()
      await postJson(
        endpointFor(`/choice-sets/${encodeURIComponent(choiceSetId)}/resolve`),
        {
          chosen_rank: resolution.chosenRank,
          chosen_at: new Date(chosenAt).toISOString(),
          time_to_decide_ms: chosenAt - presentedAt,
          dismissed_reason: resolution.dismissedReason,
          rationale: resolution.rationale,
        },
      )
    },
  }
}
