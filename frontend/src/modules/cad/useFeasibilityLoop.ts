import { useState, useEffect, useCallback, useRef } from 'react'
import { DetectedUnit, RoiMetrics } from './types'

interface FeasibilityLoopResult {
  metrics: RoiMetrics | null
  loading: boolean
  error: Error | null
}

const DEBOUNCE_MS = 1000
// Assuming backend is on localhost:8000 for dev. In prod, this should be environmental.
const WS_URL = 'ws://localhost:8000/api/v1/feasibility/ws'

export function useFeasibilityLoop(
  units: DetectedUnit[],
  _zoneCode: string | null,
): FeasibilityLoopResult {
  const [metrics, setMetrics] = useState<RoiMetrics | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const wsRef = useRef<WebSocket | null>(null)

  // Track units to debounce properly
  const unitsRef = useRef(units)
  useEffect(() => {
    unitsRef.current = units
  }, [units])

  // Initialize WebSocket on mount
  useEffect(() => {
    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen = () => {
      console.log('Feasibility Loop: WS Connected')
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.error) {
          setError(new Error(data.error))
          setLoading(false)
          return
        }
        // Transform backend response to UI metrics
        const summary = data.summary
        if (summary) {
          setMetrics({
            automationScore: 0.88, // Mock bump for WS speed
            savingsPercent: Math.round(
              (summary.estimated_achievable_gfa_sqm /
                summary.max_permissible_gfa_sqm) *
                100,
            ),
            reviewHoursSaved: 12,
            paybackWeeks: 4,
          })
        }
        setLoading(false) // Request complete
      } catch (e) {
        console.error('WS Parse Error', e)
      }
    }

    ws.onerror = (e) => {
      console.error('Feasibility Loop WS Error', e)
      setError(new Error('Connection error'))
      setLoading(false)
    }

    ws.onclose = () => {
      console.log('Feasibility Loop: WS Disconnected')
    }

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close()
      }
    }
  }, [])

  const sendUpdate = useCallback(() => {
    if (!unitsRef.current || unitsRef.current.length === 0) return
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return

    setLoading(true)
    setError(null)

    // Construct payload (same as before)
    const totalArea = unitsRef.current.reduce(
      (acc, unit) => acc + unit.areaSqm,
      0,
    )
    const payload = {
      project: {
        name: 'Live Loop WS Session',
        siteAreaSqm: totalArea * 1.5,
        landUse: 'mixed_use',
        currentGfaSqm: totalArea,
        buildEnvelope: {
          siteAreaSqm: totalArea * 1.5,
          currentGfaSqm: totalArea,
        },
      },
      selectedRuleIds: ['ura-plot-ratio', 'bca-site-coverage'],
    }

    wsRef.current.send(JSON.stringify(payload))
  }, [])

  useEffect(() => {
    const handler = setTimeout(() => {
      sendUpdate()
    }, DEBOUNCE_MS)

    return () => {
      clearTimeout(handler)
    }
  }, [units, sendUpdate])

  return { metrics, loading, error }
}
