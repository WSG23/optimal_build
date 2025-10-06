import { useCallback, useEffect, useRef, useState } from 'react'

import {
  listFinanceScenarios,
  type FinanceScenarioSummary,
} from '../../../api/finance'

export interface UseFinanceScenariosOptions {
  projectId?: number
  finProjectId?: number
}

export interface UseFinanceScenariosResult {
  scenarios: FinanceScenarioSummary[]
  loading: boolean
  error: string | null
  refresh: () => void
}

export function useFinanceScenarios(
  options: UseFinanceScenariosOptions,
): UseFinanceScenariosResult {
  const { projectId, finProjectId } = options
  const [scenarios, setScenarios] = useState<FinanceScenarioSummary[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const controllerRef = useRef<AbortController | null>(null)

  const fetchScenarios = useCallback(async () => {
    controllerRef.current?.abort()
    const controller = new AbortController()
    controllerRef.current = controller

    setLoading(true)
    setError(null)

    try {
      const response = await listFinanceScenarios(
        { projectId, finProjectId },
        { signal: controller.signal },
      )
      if (!controller.signal.aborted) {
        setScenarios(response)
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
  }, [projectId, finProjectId])

  useEffect(() => {
    void fetchScenarios()
    return () => {
      controllerRef.current?.abort()
      controllerRef.current = null
    }
  }, [fetchScenarios])

  const refresh = useCallback(() => {
    void fetchScenarios()
  }, [fetchScenarios])

  return {
    scenarios,
    loading,
    error,
    refresh,
  }
}
