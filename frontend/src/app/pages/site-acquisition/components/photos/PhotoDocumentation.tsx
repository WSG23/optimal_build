/**
 * PhotoDocumentation Component
 *
 * Combined photo capture and gallery component for property documentation.
 * Shows upload area, gallery with Original/Marketing toggle, and phase selector.
 */

import { useCallback, useEffect, useState } from 'react'
import type {
  PropertyPhoto,
  PropertyPhase,
} from '../../../../../api/siteAcquisition'
import {
  fetchPropertyPhotos,
  uploadPropertyPhoto,
  deletePropertyPhoto,
} from '../../../../../api/siteAcquisition'
import { PhotoCapture } from './PhotoCapture'
import { PhotoGallery } from './PhotoGallery'

export interface PhotoDocumentationProps {
  propertyId: string
  defaultPhase?: PropertyPhase
}

export function PhotoDocumentation({
  propertyId,
  defaultPhase = 'acquisition',
}: PhotoDocumentationProps) {
  const [photos, setPhotos] = useState<PropertyPhoto[]>([])
  const [loading, setLoading] = useState(true)
  const [phase, setPhase] = useState<PropertyPhase>(defaultPhase)
  const [error, setError] = useState<string | null>(null)

  // Fetch photos on mount and when propertyId changes
  useEffect(() => {
    let mounted = true

    async function loadPhotos() {
      if (!propertyId || propertyId === 'offline-property') {
        setPhotos([])
        setLoading(false)
        return
      }

      setLoading(true)
      setError(null)
      try {
        const result = await fetchPropertyPhotos(propertyId)
        if (mounted) {
          setPhotos(result)
        }
      } catch (err) {
        if (mounted) {
          setError('Failed to load photos')
          console.error('Error loading photos:', err)
        }
      } finally {
        if (mounted) {
          setLoading(false)
        }
      }
    }

    loadPhotos()

    return () => {
      mounted = false
    }
  }, [propertyId])

  const handleUpload = useCallback(
    async (
      file: File,
      options: { notes?: string; tags?: string[]; phase: PropertyPhase },
    ) => {
      setError(null)
      try {
        const newPhoto = await uploadPropertyPhoto(propertyId, file, options)
        if (newPhoto) {
          setPhotos((prev) => [newPhoto, ...prev])
        }
      } catch (err) {
        setError('Failed to upload photo')
        console.error('Error uploading photo:', err)
        throw err
      }
    },
    [propertyId],
  )

  const handleDelete = useCallback(
    async (photoId: string) => {
      setError(null)
      try {
        const success = await deletePropertyPhoto(propertyId, photoId)
        if (success) {
          setPhotos((prev) => prev.filter((p) => p.photoId !== photoId))
        }
      } catch (err) {
        setError('Failed to delete photo')
        console.error('Error deleting photo:', err)
        throw err
      }
    },
    [propertyId],
  )

  const isOffline = propertyId === 'offline-property'

  return (
    <section
      style={{
        background: 'var(--ob-color-surface-primary)',
        border: '1px solid var(--ob-color-border-subtle, #e5e7eb)',
        borderRadius: 'var(--ob-radius-sm)',
        padding: 'var(--ob-space-150)',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 'var(--ob-space-150)',
        }}
      >
        <div>
          <h3
            style={{
              margin: 0,
              fontSize: 'var(--ob-font-size-lg)',
              fontWeight: 'var(--ob-font-weight-semibold)',
              color: 'var(--ob-color-text-primary)',
            }}
          >
            Photo Documentation
          </h3>
          <p
            style={{
              margin: 'var(--ob-space-025) 0 0',
              fontSize: 'var(--ob-font-size-xs)',
              color: 'var(--ob-color-text-secondary)',
            }}
          >
            Capture and manage property photos with automatic watermarking
          </p>
        </div>

        {/* Phase selector */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--ob-space-050)',
          }}
        >
          <span
            style={{
              fontSize: 'var(--ob-font-size-xs)',
              color: 'var(--ob-color-text-secondary)',
            }}
          >
            Phase:
          </span>
          <select
            value={phase}
            onChange={(e) => setPhase(e.target.value as PropertyPhase)}
            style={{
              padding: 'var(--ob-space-035) var(--ob-space-075)',
              borderRadius: 'var(--ob-radius-md)',
              border: '1px solid var(--ob-color-border-default, #d1d5db)',
              fontSize: 'var(--ob-font-size-sm)',
              background: 'var(--ob-color-surface-primary)',
              cursor: 'pointer',
            }}
          >
            <option value="acquisition">Acquisition</option>
            <option value="sales">Sales</option>
          </select>
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div
          style={{
            padding: 'var(--ob-space-075) var(--ob-space-100)',
            background: 'var(--ob-color-surface-error)',
            border: '1px solid var(--ob-color-border-error, #fecaca)',
            borderRadius: 'var(--ob-radius-sm)',
            color: 'var(--ob-color-status-error)',
            fontSize: 'var(--ob-font-size-sm)',
            marginBottom: 'var(--ob-space-100)',
          }}
        >
          {error}
        </div>
      )}

      {/* Offline warning */}
      {isOffline && (
        <div
          style={{
            padding: 'var(--ob-space-075) var(--ob-space-100)',
            background: 'var(--ob-color-surface-warning)',
            border: '1px solid var(--ob-color-border-warning, #fcd34d)',
            borderRadius: 'var(--ob-radius-sm)',
            color: 'var(--ob-color-status-warning)',
            fontSize: 'var(--ob-font-size-sm)',
            marginBottom: 'var(--ob-space-100)',
          }}
        >
          Photo upload is not available in offline mode. Save the property first
          to enable photo documentation.
        </div>
      )}

      {/* Upload area */}
      <div style={{ marginBottom: 'var(--ob-space-150)' }}>
        <PhotoCapture
          propertyId={propertyId}
          phase={phase}
          onUpload={handleUpload}
          disabled={isOffline}
        />
      </div>

      {/* Gallery */}
      <PhotoGallery photos={photos} onDelete={handleDelete} loading={loading} />

      {/* Watermark info */}
      <div
        style={{
          marginTop: 'var(--ob-space-150)',
          padding: 'var(--ob-space-100)',
          background: 'var(--ob-color-surface-secondary)',
          borderRadius: 'var(--ob-radius-sm)',
          border: '1px solid var(--ob-color-border-subtle, #e5e7eb)',
        }}
      >
        <h4
          style={{
            margin: '0 0 var(--ob-space-050)',
            fontSize: 'var(--ob-font-size-sm)',
            fontWeight: 'var(--ob-font-weight-semibold)',
            color: 'var(--ob-color-text-primary)',
          }}
        >
          Watermark Information
        </h4>
        <div
          style={{
            fontSize: 'var(--ob-font-size-xs)',
            color: 'var(--ob-color-text-secondary)',
            lineHeight: 'var(--ob-line-height-normal)',
          }}
        >
          <p style={{ margin: '0 0 var(--ob-space-050)' }}>
            <strong>Original:</strong> No watermark - for internal team use
            only. Do not share externally.
          </p>
          <p style={{ margin: '0 0 var(--ob-space-050)' }}>
            <strong>Marketing:</strong> Diagonal watermark applied - safe for
            external sharing and marketing materials.
          </p>
          <p style={{ margin: 0 }}>
            <strong>Current phase:</strong>{' '}
            {phase === 'acquisition'
              ? '"Feasibility Assessment Only - Not for Construction"'
              : '"Sales Material - Subject to Final Approval"'}
          </p>
        </div>
      </div>
    </section>
  )
}
