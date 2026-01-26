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
      if (!propertyId) {
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

  const hasPropertyId = Boolean(propertyId)

  return (
    <section
      style={{
        background: 'var(--ob-color-bg-default)',
        border: '1px solid var(--ob-color-border-subtle)',
        borderRadius: 'var(--ob-radius-sm)',
        padding: 'var(--ob-space-300)',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 'var(--ob-space-300)',
        }}
      >
        <div>
          <h3
            style={{
              margin: 0,
              fontSize: '1.125rem',
              fontWeight: 600,
              color: '#1f2937',
            }}
          >
            Photo Documentation
          </h3>
          <p
            style={{
              margin: 'var(--ob-space-50) 0 0',
              fontSize: '0.8125rem',
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
            gap: 'var(--ob-space-100)',
          }}
        >
          <span
            style={{
              fontSize: '0.8125rem',
              color: 'var(--ob-color-text-secondary)',
            }}
          >
            Phase:
          </span>
          <select
            value={phase}
            onChange={(e) => setPhase(e.target.value as PropertyPhase)}
            style={{
              padding: 'var(--ob-space-50) 0.75rem',
              borderRadius: 'var(--ob-radius-md)',
              border: '1px solid var(--ob-color-border-default)',
              fontSize: '0.875rem',
              background: 'var(--ob-color-bg-default)',
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
            padding: 'var(--ob-space-150) 1rem',
            background: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: 'var(--ob-radius-sm)',
            color: 'var(--ob-color-error)',
            fontSize: '0.875rem',
            marginBottom: 'var(--ob-space-200)',
          }}
        >
          {error}
        </div>
      )}

      {/* Upload area */}
      <div style={{ marginBottom: 'var(--ob-space-300)' }}>
        <PhotoCapture
          propertyId={propertyId}
          phase={phase}
          onUpload={handleUpload}
          disabled={!hasPropertyId}
        />
      </div>

      {/* Gallery */}
      <PhotoGallery photos={photos} onDelete={handleDelete} loading={loading} />

      {/* Watermark info */}
      <div
        style={{
          marginTop: 'var(--ob-space-300)',
          padding: 'var(--ob-space-200)',
          background: 'var(--ob-color-bg-muted)',
          borderRadius: 'var(--ob-radius-sm)',
          border: '1px solid var(--ob-color-border-subtle)',
        }}
      >
        <h4
          style={{
            margin: '0 0 0.5rem',
            fontSize: '0.875rem',
            fontWeight: 600,
            color: 'var(--ob-color-text-primary)',
          }}
        >
          Watermark Information
        </h4>
        <div
          style={{
            fontSize: '0.8125rem',
            color: 'var(--ob-color-text-secondary)',
            lineHeight: 1.5,
          }}
        >
          <p style={{ margin: '0 0 0.5rem' }}>
            <strong>Original:</strong> No watermark - for internal team use
            only. Do not share externally.
          </p>
          <p style={{ margin: '0 0 0.5rem' }}>
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
