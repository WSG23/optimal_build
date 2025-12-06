import { useCallback, useEffect, useRef, useState } from 'react'

import { type FeasibilityAssessmentRequest, submitFeasibilityAssessment } from '../../../api/feasibility'
import { type BuildableSummary } from '../../../api/buildable'
import type { PendingPayload, WizardStatus } from '../types'
import { DEBOUNCE_MS } from '../types'
import { anonymiseAddress } from '../utils/formatters'

interface UseFeasibilityComputeOptions {
  t: (key: string, options?: Record<string, unknown>) => string
}

interface UseFeasibilityComputeResult {
  result: BuildableSummary | null
  status: WizardStatus
  errorMessage: string | null
  liveAnnouncement: string
  payload: PendingPayload | null
  setPayload: (payload: PendingPayload | null) => void
  updatePayloadAssumptions: (typFloorToFloorM: number, efficiencyRatio: number) => void
}

export function useFeasibilityCompute({
  t,
}: UseFeasibilityComputeOptions): UseFeasibilityComputeResult {
  const [payload, setPayload] = useState<PendingPayload | null>(null)
  const [result, setResult] = useState<BuildableSummary | null>(null)
  const [status, setStatus] = useState<WizardStatus>('idle')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [liveAnnouncement, setLiveAnnouncement] = useState('')

  const abortControllerRef = useRef<AbortController | null>(null)
  const debounceRef = useRef<number | null>(null)

  const dispatchTelemetry = useCallback(
    (
      durationMs: number,
      outcome: 'success' | 'error',
      zoneCode: string | null,
      address: string,
    ) => {
      const detail = {
        event: 'feasibility.compute',
        durationMs,
        status: outcome,
        zoneCode,
        addressPreview: anonymiseAddress(address),
      }
      window.dispatchEvent(new CustomEvent('feasibility.compute', { detail }))
    },
    [],
  )

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort()
      if (debounceRef.current !== null) {
        clearTimeout(debounceRef.current)
      }
    }
  }, [])

  useEffect(() => {
    if (!payload) {
      return () => {}
    }
    console.log('useFeasibilityCompute: Payload changed:', payload)

    if (debounceRef.current !== null) {
      clearTimeout(debounceRef.current)
    }
    abortControllerRef.current?.abort()
    const controller = new AbortController()
    abortControllerRef.current = controller

    setStatus('loading')
    setErrorMessage(null)

    const startTime =
      typeof performance !== 'undefined' ? performance.now() : Date.now()

    debounceRef.current = window.setTimeout(() => {
      console.log('useFeasibilityCompute: Debounce fired. Submitting payload.')
      // Map PendingPayload to FeasibilityAssessmentRequest
      const requestPayload: FeasibilityAssessmentRequest = {
        project: {
          name: payload.name || 'Project',
          siteAddress: payload.address,
          siteAreaSqm: payload.siteAreaSqm,
          landUse: payload.landUse,
          typFloorToFloorM: payload.typFloorToFloorM,
          efficiencyRatio: payload.efficiencyRatio,
        },
        selectedRuleIds: [], // Default to empty or select all
      }

      submitFeasibilityAssessment(requestPayload, controller.signal)
        .then((response) => {
          console.log('useFeasibilityCompute: Success response received', response)
          const duration =
            (typeof performance !== 'undefined'
              ? performance.now()
              : Date.now()) - startTime

          dispatchTelemetry(
            duration,
            'success',
            'URA-ZONING-TODO',
            payload.address,
          )

          // Map FeasibilityAssessmentResponse to BuildableSummary
          const mappedBox: BuildableSummary = {
            inputKind: 'address',
            zoneCode: 'URA-ZONING-TODO',
            overlays: [],
            advisoryHints: response.recommendations || [],
            metrics: {
              gfaCapM2: response.summary.maxPermissibleGfaSqm,
              floorsMax: 0,
              footprintM2: 0,
              nsaEstM2: response.summary.estimatedAchievableGfaSqm,
            },
            zoneSource: { kind: 'unknown' },
            rules: response.rules.map((r, index) => ({
              id: index,
              authority: r.authority,
              parameterKey: r.parameterKey,
              operator: r.operator,
              value: r.value,
              unit: r.unit ?? undefined,
              provenance: {
                ruleId: index,
                clauseRef: r.topic,
              },
            })),
          }

          setResult(mappedBox)

          setStatus('success')

          setLiveAnnouncement(
            t('wizard.accessibility.updated', {
              zone: mappedBox.zoneCode,
              overlays: mappedBox.overlays.length,
            }),
          )
        })
        .catch((error) => {
          console.error('useFeasibilityCompute: Error caught', error)
          if (error instanceof DOMException && error.name === 'AbortError') {
            return
          }
          const duration =
            (typeof performance !== 'undefined'
              ? performance.now()
              : Date.now()) - startTime
          dispatchTelemetry(duration, 'error', null, payload.address)
          setStatus('error')
          setErrorMessage(
            error instanceof Error ? error.message : t('wizard.errors.generic'),
          )
        })
        .finally(() => {
          debounceRef.current = null
        })

    }, DEBOUNCE_MS)

    return () => {
      controller.abort()
      if (debounceRef.current !== null) {
        clearTimeout(debounceRef.current)
        debounceRef.current = null
      }
    }
  }, [payload, dispatchTelemetry, t])

  const updatePayloadAssumptions = useCallback(
    (typFloorToFloorM: number, efficiencyRatio: number) => {
      setPayload((previous) => {
        if (!previous) {
          return previous
        }
        if (
          previous.typFloorToFloorM === typFloorToFloorM &&
          previous.efficiencyRatio === efficiencyRatio
        ) {
          return previous
        }
        return {
          ...previous,
          typFloorToFloorM,
          efficiencyRatio,
        }
      })
    },
    [],
  )

  return {
    result,
    status,
    errorMessage,
    liveAnnouncement,
    payload,
    setPayload,
    updatePayloadAssumptions,
  }
}
