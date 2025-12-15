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
        background: '#fff',
        border: '1px solid #e5e7eb',
        borderRadius: '4px',
        padding: '1.5rem',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '1.5rem',
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
              margin: '0.25rem 0 0',
              fontSize: '0.8125rem',
              color: '#6b7280',
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
            gap: '0.5rem',
          }}
        >
          <span
            style={{
              fontSize: '0.8125rem',
              color: '#6b7280',
            }}
          >
            Phase:
          </span>
          <select
            value={phase}
            onChange={(e) => setPhase(e.target.value as PropertyPhase)}
            style={{
              padding: '0.375rem 0.75rem',
              borderRadius: '6px',
              border: '1px solid #d1d5db',
              fontSize: '0.875rem',
              background: '#fff',
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
            padding: '0.75rem 1rem',
            background: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '4px',
            color: '#dc2626',
            fontSize: '0.875rem',
            marginBottom: '1rem',
          }}
        >
          {error}
        </div>
      )}

      {/* Offline warning */}
      {isOffline && (
        <div
          style={{
            padding: '0.75rem 1rem',
            background: '#fffbeb',
            border: '1px solid #fcd34d',
            borderRadius: '4px',
            color: '#92400e',
            fontSize: '0.875rem',
            marginBottom: '1rem',
          }}
        >
          Photo upload is not available in offline mode. Save the property first
          to enable photo documentation.
        </div>
      )}

      {/* Upload area */}
      <div style={{ marginBottom: '1.5rem' }}>
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
          marginTop: '1.5rem',
          padding: '1rem',
          background: '#f9fafb',
          borderRadius: '4px',
          border: '1px solid #e5e7eb',
        }}
      >
        <h4
          style={{
            margin: '0 0 0.5rem',
            fontSize: '0.875rem',
            fontWeight: 600,
            color: '#374151',
          }}
        >
          Watermark Information
        </h4>
        <div
          style={{
            fontSize: '0.8125rem',
            color: '#6b7280',
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
