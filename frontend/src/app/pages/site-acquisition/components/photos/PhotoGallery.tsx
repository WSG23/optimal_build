/**
 * PhotoGallery Component
 *
 * Displays uploaded photos with toggle to switch between Original and Marketing (watermarked) views.
 * Shows photo metadata including tags, notes, and capture information.
 */

import { useCallback, useState } from 'react'
import type {
  PropertyPhoto,
  PhotoVersion,
} from '../../../../../api/siteAcquisition'
import { getPhotoVersionUrl } from '../../../../../api/siteAcquisition'

export type ViewMode = 'original' | 'marketing'

export interface PhotoGalleryProps {
  photos: PropertyPhoto[]
  onDelete?: (photoId: string) => Promise<void>
  loading?: boolean
}

export function PhotoGallery({
  photos,
  onDelete,
  loading = false,
}: PhotoGalleryProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('original')
  const [selectedPhoto, setSelectedPhoto] = useState<PropertyPhoto | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const handleDelete = useCallback(
    async (photo: PropertyPhoto) => {
      if (!onDelete) return
      if (!confirm('Delete this photo?')) return

      setDeletingId(photo.photoId)
      try {
        await onDelete(photo.photoId)
        if (selectedPhoto?.photoId === photo.photoId) {
          setSelectedPhoto(null)
        }
      } finally {
        setDeletingId(null)
      }
    },
    [onDelete, selectedPhoto],
  )

  const getDisplayUrl = useCallback(
    (photo: PropertyPhoto): string | null => {
      const version: PhotoVersion =
        viewMode === 'marketing' ? 'marketing' : 'original'
      return getPhotoVersionUrl(photo, version)
    },
    [viewMode],
  )

  const getThumbnailUrl = useCallback((photo: PropertyPhoto): string | null => {
    return getPhotoVersionUrl(photo, 'thumbnail')
  }, [])

  if (loading) {
    return (
      <div
        style={{
          padding: '2rem',
          textAlign: 'center',
          color: '#6b7280',
        }}
      >
        Loading photos...
      </div>
    )
  }

  if (photos.length === 0) {
    return (
      <div
        style={{
          padding: '2rem',
          textAlign: 'center',
          color: '#6b7280',
          background: '#f9fafb',
          borderRadius: '4px',
          border: '1px dashed #d1d5db',
        }}
      >
        <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>
          {'\uD83D\uDDBC\uFE0F'}
        </div>
        <p style={{ margin: 0, fontWeight: 500 }}>No photos yet</p>
        <p style={{ margin: '0.25rem 0 0', fontSize: '0.8125rem' }}>
          Upload photos to document this property
        </p>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {/* View mode toggle */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0.5rem 0',
        }}
      >
        <span
          style={{
            fontSize: '0.875rem',
            fontWeight: 600,
            color: '#374151',
          }}
        >
          {photos.length} photo{photos.length !== 1 ? 's' : ''}
        </span>

        <div
          style={{
            display: 'inline-flex',
            background: '#f3f4f6',
            borderRadius: '9999px',
            padding: '0.25rem',
          }}
        >
          <button
            type="button"
            onClick={() => setViewMode('original')}
            style={{
              padding: '0.375rem 0.875rem',
              borderRadius: '9999px',
              border: 'none',
              background: viewMode === 'original' ? '#fff' : 'transparent',
              color: viewMode === 'original' ? '#1f2937' : '#6b7280',
              fontSize: '0.8125rem',
              fontWeight: 500,
              cursor: 'pointer',
              boxShadow:
                viewMode === 'original' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
              transition: 'all 0.15s ease',
            }}
          >
            Original
          </button>
          <button
            type="button"
            onClick={() => setViewMode('marketing')}
            style={{
              padding: '0.375rem 0.875rem',
              borderRadius: '9999px',
              border: 'none',
              background: viewMode === 'marketing' ? '#fff' : 'transparent',
              color: viewMode === 'marketing' ? '#1f2937' : '#6b7280',
              fontSize: '0.8125rem',
              fontWeight: 500,
              cursor: 'pointer',
              boxShadow:
                viewMode === 'marketing' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
              transition: 'all 0.15s ease',
            }}
          >
            Marketing
          </button>
        </div>
      </div>

      {/* Explanation text */}
      <p
        style={{
          margin: 0,
          fontSize: '0.75rem',
          color: '#9ca3af',
          fontStyle: 'italic',
        }}
      >
        {viewMode === 'original'
          ? 'Viewing original photos (no watermark) - for internal use only'
          : 'Viewing marketing versions with watermark - safe for external sharing'}
      </p>

      {/* Photo grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))',
          gap: '0.75rem',
        }}
      >
        {photos.map((photo) => {
          const thumbnailUrl = getThumbnailUrl(photo)
          const isDeleting = deletingId === photo.photoId

          return (
            <div
              key={photo.photoId}
              style={{
                position: 'relative',
                aspectRatio: '1',
                borderRadius: '4px',
                overflow: 'hidden',
                background: '#f3f4f6',
                cursor: 'pointer',
                opacity: isDeleting ? 0.5 : 1,
              }}
              onClick={() => setSelectedPhoto(photo)}
              onKeyDown={(e) => e.key === 'Enter' && setSelectedPhoto(photo)}
              role="button"
              tabIndex={0}
            >
              {thumbnailUrl ? (
                <img
                  src={thumbnailUrl}
                  alt={photo.notes || 'Property photo'}
                  style={{
                    width: '100%',
                    height: '100%',
                    objectFit: 'cover',
                  }}
                />
              ) : (
                <div
                  style={{
                    width: '100%',
                    height: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#9ca3af',
                    fontSize: '2rem',
                  }}
                >
                  {'\uD83D\uDDBC\uFE0F'}
                </div>
              )}

              {/* Auto-tags overlay */}
              {photo.autoTags.length > 0 && (
                <div
                  style={{
                    position: 'absolute',
                    bottom: 0,
                    left: 0,
                    right: 0,
                    padding: '0.25rem 0.5rem',
                    background: 'linear-gradient(transparent, rgba(0,0,0,0.7))',
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: '0.25rem',
                  }}
                >
                  {photo.autoTags.slice(0, 2).map((tag) => (
                    <span
                      key={tag}
                      style={{
                        padding: '0.125rem 0.375rem',
                        background: 'rgba(255,255,255,0.2)',
                        borderRadius: '4px',
                        fontSize: '0.625rem',
                        color: '#fff',
                      }}
                    >
                      {tag.replace(/_/g, ' ')}
                    </span>
                  ))}
                </div>
              )}

              {/* Delete button */}
              {onDelete && (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleDelete(photo)
                  }}
                  disabled={isDeleting}
                  style={{
                    position: 'absolute',
                    top: '0.25rem',
                    right: '0.25rem',
                    width: '24px',
                    height: '24px',
                    borderRadius: '50%',
                    border: 'none',
                    background: 'rgba(0,0,0,0.6)',
                    color: '#fff',
                    fontSize: '0.875rem',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                  title="Delete photo"
                >
                  {'\u00D7'}
                </button>
              )}
            </div>
          )
        })}
      </div>

      {/* Lightbox / Detail view */}
      {selectedPhoto && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.9)',
            zIndex: 1000,
            display: 'flex',
            flexDirection: 'column',
            padding: '1rem',
          }}
          onClick={() => setSelectedPhoto(null)}
          onKeyDown={(e) => e.key === 'Escape' && setSelectedPhoto(null)}
          role="dialog"
          aria-modal="true"
        >
          {/* Header */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '1rem',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ color: '#fff' }}>
              <div style={{ fontWeight: 600 }}>
                {selectedPhoto.notes || 'Property Photo'}
              </div>
              {selectedPhoto.captureTimestamp && (
                <div style={{ fontSize: '0.8125rem', color: '#9ca3af' }}>
                  {new Date(selectedPhoto.captureTimestamp).toLocaleString()}
                </div>
              )}
            </div>

            <div style={{ display: 'flex', gap: '0.5rem' }}>
              {/* View toggle in lightbox */}
              <div
                style={{
                  display: 'inline-flex',
                  background: 'rgba(255,255,255,0.1)',
                  borderRadius: '9999px',
                  padding: '0.25rem',
                }}
              >
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation()
                    setViewMode('original')
                  }}
                  style={{
                    padding: '0.375rem 0.75rem',
                    borderRadius: '9999px',
                    border: 'none',
                    background:
                      viewMode === 'original'
                        ? 'rgba(255,255,255,0.2)'
                        : 'transparent',
                    color: '#fff',
                    fontSize: '0.75rem',
                    fontWeight: 500,
                    cursor: 'pointer',
                  }}
                >
                  Original
                </button>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation()
                    setViewMode('marketing')
                  }}
                  style={{
                    padding: '0.375rem 0.75rem',
                    borderRadius: '9999px',
                    border: 'none',
                    background:
                      viewMode === 'marketing'
                        ? 'rgba(255,255,255,0.2)'
                        : 'transparent',
                    color: '#fff',
                    fontSize: '0.75rem',
                    fontWeight: 500,
                    cursor: 'pointer',
                  }}
                >
                  Marketing
                </button>
              </div>

              <button
                type="button"
                onClick={() => setSelectedPhoto(null)}
                style={{
                  padding: '0.5rem 1rem',
                  borderRadius: '4px',
                  border: 'none',
                  background: 'rgba(255,255,255,0.1)',
                  color: '#fff',
                  fontSize: '0.875rem',
                  cursor: 'pointer',
                }}
              >
                Close
              </button>
            </div>
          </div>

          {/* Image */}
          <div
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              overflow: 'hidden',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {getDisplayUrl(selectedPhoto) ? (
              <img
                src={getDisplayUrl(selectedPhoto)!}
                alt={selectedPhoto.notes || 'Property photo'}
                style={{
                  maxWidth: '100%',
                  maxHeight: '100%',
                  objectFit: 'contain',
                  borderRadius: '4px',
                }}
              />
            ) : (
              <div style={{ color: '#9ca3af' }}>Image not available</div>
            )}
          </div>

          {/* Footer with tags */}
          {selectedPhoto.autoTags.length > 0 && (
            <div
              style={{
                marginTop: '1rem',
                display: 'flex',
                flexWrap: 'wrap',
                gap: '0.5rem',
                justifyContent: 'center',
              }}
              onClick={(e) => e.stopPropagation()}
            >
              {selectedPhoto.autoTags.map((tag) => (
                <span
                  key={tag}
                  style={{
                    padding: '0.25rem 0.75rem',
                    background: 'rgba(255,255,255,0.1)',
                    borderRadius: '9999px',
                    fontSize: '0.75rem',
                    color: '#fff',
                  }}
                >
                  {tag.replace(/_/g, ' ')}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
