/**
 * usePropertyCapture Hook
 *
 * Manages property capture state including:
 * - Selected development scenarios
 * - Capture loading/error state
 * - Captured property result
 * - Session storage for asset mix snapshots
 */

import { useCallback, useState } from 'react'
import {
  capturePropertyForDevelopment,
  type DevelopmentScenario,
  type SiteAcquisitionResult,
  type GeometryDetailLevel,
  type PreviewJobInfo,
} from '../../../../api/siteAcquisition'

// ============================================================================
// Types
// ============================================================================

export interface UsePropertyCaptureOptions {
  previewDetailLevel: GeometryDetailLevel
  onPreviewJobReceived?: (job: PreviewJobInfo | null) => void
}

export interface UsePropertyCaptureReturn {
  // State
  selectedScenarios: DevelopmentScenario[]
  isCapturing: boolean
  error: string | null
  capturedProperty: SiteAcquisitionResult | null

  // Handlers
  toggleScenario: (scenario: DevelopmentScenario) => void
  handleCapture: (
    latitude: string,
    longitude: string,
    jurisdictionCode: string,
  ) => Promise<void>
  setCapturedProperty: (property: SiteAcquisitionResult | null) => void
  setError: (error: string | null) => void
}

// ============================================================================
// Helpers
// ============================================================================

function buildAssetMixStorageKey(propertyId: string): string {
  return `developer-asset-mix:${propertyId}`
}

// ============================================================================
// Hook Implementation
// ============================================================================

export function usePropertyCapture(
  options: UsePropertyCaptureOptions,
): UsePropertyCaptureReturn {
  const { previewDetailLevel, onPreviewJobReceived } = options

  const [selectedScenarios, setSelectedScenarios] = useState<
    DevelopmentScenario[]
  >([])
  const [isCapturing, setIsCapturing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [capturedProperty, setCapturedProperty] =
    useState<SiteAcquisitionResult | null>(null)

  const toggleScenario = useCallback((scenario: DevelopmentScenario) => {
    setSelectedScenarios((prev) =>
      prev.includes(scenario)
        ? prev.filter((s) => s !== scenario)
        : [...prev, scenario],
    )
  }, [])

  const handleCapture = useCallback(
    async (latitude: string, longitude: string, jurisdictionCode: string) => {
      const lat = parseFloat(latitude)
      const lon = parseFloat(longitude)

      if (isNaN(lat) || isNaN(lon)) {
        setError('Please enter valid coordinates')
        return
      }

      if (selectedScenarios.length === 0) {
        setError('Please select at least one development scenario')
        return
      }

      setIsCapturing(true)
      setError(null)

      try {
        const result = await capturePropertyForDevelopment({
          latitude: lat,
          longitude: lon,
          developmentScenarios: selectedScenarios,
          previewDetailLevel,
          jurisdictionCode,
        })

        setCapturedProperty(result)

        // Notify parent about preview job
        if (onPreviewJobReceived) {
          onPreviewJobReceived(result.previewJobs?.[0] ?? null)
        }

        // Persist to session storage
        if (result.propertyId) {
          try {
            const propertyLabel =
              result.propertyInfo?.propertyName?.trim() ||
              result.address?.fullAddress?.trim() ||
              null
            sessionStorage.setItem(
              buildAssetMixStorageKey(result.propertyId),
              JSON.stringify({
                optimizations: result.optimizations,
                buildEnvelope: result.buildEnvelope,
                financialSummary: result.financialSummary,
                visualization: result.visualization,
                propertyInfo: result.propertyInfo,
                address: result.address,
                metadata: {
                  propertyId: result.propertyId,
                  propertyName: propertyLabel,
                  capturedAt: result.timestamp ?? new Date().toISOString(),
                },
              }),
            )
          } catch (storageError) {
            console.warn('Unable to persist asset mix snapshot', storageError)
          }
        }
      } catch (err) {
        setError(
          err instanceof Error ? err.message : 'Failed to capture property',
        )
      } finally {
        setIsCapturing(false)
      }
    },
    [selectedScenarios, previewDetailLevel, onPreviewJobReceived],
  )

  return {
    selectedScenarios,
    isCapturing,
    error,
    capturedProperty,
    toggleScenario,
    handleCapture,
    setCapturedProperty,
    setError,
  }
}
