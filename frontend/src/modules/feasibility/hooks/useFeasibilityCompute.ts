import { useCallback, useEffect, useRef, useState } from 'react'

import { fetchBuildable, type BuildableSummary } from '../../../api/buildable'
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
      fetchBuildable(payload, { signal: controller.signal })
        .then((response) => {
          const duration =
            (typeof performance !== 'undefined'
              ? performance.now()
              : Date.now()) - startTime

          dispatchTelemetry(
            duration,
            'success',
            response.zoneCode,
            payload.address,
          )
          setResult(response)

          if (!response.zoneCode) {
            setStatus('empty')
            setLiveAnnouncement(t('wizard.accessibility.noZone'))
            return
          }

          if (response.rules.length === 0) {
            setStatus('partial')
          } else {
            setStatus('success')
          }

          setLiveAnnouncement(
            t('wizard.accessibility.updated', {
              zone: response.zoneCode,
              overlays: response.overlays.length,
            }),
          )
        })
        .catch((error) => {
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
