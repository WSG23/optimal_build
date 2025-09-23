import { useCallback, useEffect, useRef, useState } from 'react'

import {
  runFinanceFeasibility,
  type FinanceFeasibilityRequest,
  type FinanceScenarioSummary,
} from '../../../api/finance'

export interface UseFinanceFeasibilityResult {
  scenarios: FinanceScenarioSummary[]
  loading: boolean
  error: string | null
  refresh: () => void
}

export function useFinanceFeasibility(
  requests: readonly FinanceFeasibilityRequest[],
): UseFinanceFeasibilityResult {
  const [scenarios, setScenarios] = useState<FinanceScenarioSummary[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const controllerRef = useRef<AbortController | null>(null)

  const fetchScenarios = useCallback(async () => {
    controllerRef.current?.abort()
    if (requests.length === 0) {
      controllerRef.current = null
      setScenarios([])
      setLoading(false)
      setError(null)
      return
    }

    const controller = new AbortController()
    controllerRef.current = controller

    setLoading(true)
    setError(null)

    try {
      const responses = await Promise.all(
        requests.map((request) =>
          runFinanceFeasibility(request, { signal: controller.signal }),
        ),
      )
      if (!controller.signal.aborted) {
        setScenarios(responses)
      }
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        return
      }
      if (!controller.signal.aborted) {
        setScenarios([])
        setError(err instanceof Error ? err.message : String(err))
      }
    } finally {
      if (!controller.signal.aborted) {
        setLoading(false)
      }
      if (controllerRef.current === controller) {
        controllerRef.current = null
      }
    }
  }, [requests])

  useEffect(() => {
    fetchScenarios()
    return () => {
      controllerRef.current?.abort()
      controllerRef.current = null
    }
  }, [fetchScenarios])

  return {
    scenarios,
    loading,
    error,
    refresh: fetchScenarios,
  }
}
