import { useState, useEffect, useCallback, useRef } from 'react'
import { DetectedUnit, RoiMetrics } from './types'
import { buildUrl } from '../../api/utils/baseUrl'

interface FeasibilityLoopResult {
  metrics: RoiMetrics | null
  loading: boolean
  error: Error | null
}

const DEBOUNCE_MS = 1000
const WS_PATH = '/api/v1/feasibility/ws'

function buildWebSocketUrl(path: string): string {
  const httpUrl = buildUrl(path)
  if (/^https?:/i.test(httpUrl)) {
    const url = new URL(httpUrl)
    url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
    return url.toString()
  }

  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const normalizedPath = httpUrl.startsWith('/') ? httpUrl : `/${httpUrl}`
    return `${protocol}//${host}${normalizedPath}`
  }

  return httpUrl
}

const WS_URL = buildWebSocketUrl(WS_PATH)

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
          const maxGfa = Number(summary.max_permissible_gfa_sqm || 0)
          const achievable = Number(summary.estimated_achievable_gfa_sqm || 0)
          const savingsPercent =
            maxGfa > 0 ? Math.round((achievable / maxGfa) * 100) : 0
          const automationScore =
            typeof data.optimizer_confidence === 'number'
              ? Math.min(1, Math.max(0, data.optimizer_confidence))
              : 0

          setMetrics({
            automationScore,
            savingsPercent,
            reviewHoursSaved: 0,
            paybackWeeks: 0,
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
  }, [_zoneCode])

  const sendUpdate = useCallback(() => {
    if (!unitsRef.current || unitsRef.current.length === 0) return
    const zoneCode = _zoneCode?.trim()
    if (!zoneCode) {
      setError(new Error('Zone code required for feasibility loop'))
      return
    }
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return

    setLoading(true)
    setError(null)

    // Construct payload (same as before)
    const totalArea = unitsRef.current.reduce(
      (acc, unit) => acc + unit.areaSqm,
      0,
    )
    const siteAreaSqm = totalArea
    const payload = {
      project: {
        name: zoneCode,
        siteAddress: zoneCode,
        siteAreaSqm,
        landUse: zoneCode,
        targetGrossFloorAreaSqm: totalArea,
        buildEnvelope: {
          siteAreaSqm,
          currentGfaSqm: totalArea,
        },
      },
      selectedRuleIds: [],
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
