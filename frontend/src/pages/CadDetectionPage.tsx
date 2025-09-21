import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import type { AuditEvent, OverlayInsights } from '../api/client'
import { AppLayout } from '../App'
import { useApiClient } from '../api/client'
import { useLocale } from '../i18n/LocaleContext'
import AuditTimelinePanel from '../modules/cad/AuditTimelinePanel'
import BulkReviewControls from '../modules/cad/BulkReviewControls'
import CadDetectionPreview from '../modules/cad/CadDetectionPreview'
import ExportDialog from '../modules/cad/ExportDialog'
import LayerTogglePanel from '../modules/cad/LayerTogglePanel'
import ZoneLockControls from '../modules/cad/ZoneLockControls'
import { DetectionStatus, DetectedUnit } from '../modules/cad/types'

const INITIAL_UNITS: DetectedUnit[] = [
  { id: 'L01-01', floor: 1, unitLabel: '#01-01', areaSqm: 82, status: 'source' },
  { id: 'L01-02', floor: 1, unitLabel: '#01-02', areaSqm: 79, status: 'pending' },
  { id: 'L02-01', floor: 2, unitLabel: '#02-01', areaSqm: 85, status: 'approved' },
  { id: 'L02-02', floor: 2, unitLabel: '#02-02', areaSqm: 88, status: 'pending' },
  { id: 'L03-01', floor: 3, unitLabel: '#03-01', areaSqm: 92, status: 'rejected' },
  { id: 'L03-02', floor: 3, unitLabel: '#03-02', areaSqm: 90, status: 'pending' },
]

export function CadDetectionPage() {
  const apiClient = useApiClient()
  const { strings } = useLocale()
  const [zoneCode, setZoneCode] = useState('RA')
  const [units, setUnits] = useState<DetectedUnit[]>(INITIAL_UNITS)
  const [activeLayers, setActiveLayers] = useState<DetectionStatus[]>([
    'source',
    'pending',
    'approved',
    'rejected',
  ])
  const [locked, setLocked] = useState(false)
  const [insights, setInsights] = useState<OverlayInsights | null>(null)
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([])
  const [auditLoading, setAuditLoading] = useState(false)
  const cancelRef = useRef<(() => void) | null>(null)

  useEffect(() => {
    let cancelled = false
    setAuditLoading(true)
    apiClient
      .listAuditTrail()
      .then((events) => {
        if (!cancelled) {
          setAuditEvents(events)
        }
      })
      .finally(() => {
        if (!cancelled) {
          setAuditLoading(false)
        }
      })
    return () => {
      cancelled = true
    }
  }, [apiClient])

  const refreshOverlays = useCallback(
    async (code: string) => {
      try {
        const data = await apiClient.getOverlayInsights({ zoneCode: code })
        setInsights(data)
      } catch (error) {
        setInsights({ zoneCode: code, overlays: [], advisoryHints: [String(error)] })
      }
    },
    [apiClient],
  )

  useEffect(() => {
    cancelRef.current?.()
    refreshOverlays(zoneCode)
    cancelRef.current = apiClient.subscribeToOverlayUpdates({
      zoneCode,
      onUpdate: setInsights,
      intervalMs: 8000,
    })
    return () => {
      cancelRef.current?.()
    }
  }, [apiClient, refreshOverlays, zoneCode])

  const pendingCount = useMemo(() => units.filter((unit) => unit.status === 'pending').length, [units])

  const visibleUnits = useMemo(
    () => units.filter((unit) => activeLayers.includes(unit.status)),
    [units, activeLayers],
  )

  const handleLayerToggle = useCallback((_: DetectionStatus, next: DetectionStatus[]) => {
    setActiveLayers(next)
  }, [])

  const handleApproveAll = useCallback(() => {
    if (locked) {
      return
    }
    setUnits((prev) =>
      prev.map((unit) => (unit.status === 'pending' ? { ...unit, status: 'approved' } : unit)),
    )
  }, [locked])

  const handleRejectAll = useCallback(() => {
    if (locked) {
      return
    }
    setUnits((prev) =>
      prev.map((unit) => (unit.status === 'pending' ? { ...unit, status: 'rejected' } : unit)),
    )
  }, [locked])

  const handleExport = useCallback((format: string) => {
    console.info(`Exporting review pack as ${format}`)
  }, [])

  return (
    <AppLayout title={strings.detection.title} subtitle={strings.detection.subtitle}>
      <div className="cad-detection__toolbar">
        <label>
          <span>{strings.uploader.zone}</span>
          <select value={zoneCode} onChange={(event) => setZoneCode(event.target.value)} disabled={locked}>
            <option value="RA">RA</option>
            <option value="RCR">RCR</option>
            <option value="CBD">CBD</option>
          </select>
        </label>
      </div>

      <CadDetectionPreview
        units={visibleUnits}
        overlays={insights?.overlays ?? []}
        hints={insights?.advisoryHints ?? []}
        zoneCode={insights?.zoneCode ?? zoneCode}
        locked={locked}
      />

      <div className="cad-detection__grid">
        <LayerTogglePanel activeLayers={activeLayers} onToggle={handleLayerToggle} />
        <BulkReviewControls
          pendingCount={pendingCount}
          onApproveAll={handleApproveAll}
          onRejectAll={handleRejectAll}
          disabled={locked}
        />
        <ZoneLockControls locked={locked} onToggle={setLocked} />
        <ExportDialog onExport={handleExport} disabled={pendingCount > 0} />
      </div>

      <AuditTimelinePanel events={auditEvents} loading={auditLoading} />
    </AppLayout>
  )
}

export default CadDetectionPage
