/**
 * PhotoGallery Component
 *
 * Displays uploaded photos with toggle to switch between Original and Marketing (watermarked) views.
 * Shows photo metadata including tags, notes, and capture information.
 */

import { useCallback, useEffect, useRef, useState } from 'react'
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
  const lightboxRef = useRef<HTMLDivElement>(null)
  const previousFocusRef = useRef<HTMLElement | null>(null)

  const isLightboxOpen = selectedPhoto !== null

  useEffect(() => {
    if (!isLightboxOpen) return

    previousFocusRef.current = document.activeElement as HTMLElement | null

    const timer = requestAnimationFrame(() => {
      const dialog = lightboxRef.current
      if (!dialog) return
      const focusable = dialog.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
      )
      if (focusable.length > 0) focusable[0].focus()
    })

    return () => {
      cancelAnimationFrame(timer)
      previousFocusRef.current?.focus()
    }
  }, [isLightboxOpen])

  useEffect(() => {
    if (!isLightboxOpen) return

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        setSelectedPhoto(null)
        return
      }
      if (e.key !== 'Tab') return

      const dialog = lightboxRef.current
      if (!dialog) return

      const focusable = dialog.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
      )
      if (focusable.length === 0) return

      const first = focusable[0]
      const last = focusable[focusable.length - 1]

      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault()
          last.focus()
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault()
          first.focus()
        }
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isLightboxOpen])

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
          padding: 'var(--ob-space-200)',
          textAlign: 'center',
          color: 'var(--ob-color-text-secondary)',
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
          padding: 'var(--ob-space-200)',
          textAlign: 'center',
          color: 'var(--ob-color-text-secondary)',
          background: 'var(--ob-color-surface-secondary)',
          borderRadius: 'var(--ob-radius-sm)',
          border: '1px dashed var(--ob-color-border-subtle)',
        }}
      >
        <div
          style={{
            fontSize: 'var(--ob-font-size-3xl)',
            marginBottom: 'var(--ob-space-050)',
          }}
        >
          {'\uD83D\uDDBC\uFE0F'}
        </div>
        <p style={{ margin: 0, fontWeight: 'var(--ob-font-weight-medium)' }}>
          No photos yet
        </p>
        <p
          style={{
            margin: 'var(--ob-space-025) 0 0',
            fontSize: 'var(--ob-font-size-xs)',
          }}
        >
          Upload photos to document this property
        </p>
      </div>
    )
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--ob-space-100)',
      }}
    >
      {/* View mode toggle */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: 'var(--ob-space-050) 0',
        }}
      >
        <span
          style={{
            fontSize: 'var(--ob-font-size-sm)',
            fontWeight: 'var(--ob-font-weight-semibold)',
            color: 'var(--ob-color-text-primary)',
          }}
        >
          {photos.length} photo{photos.length !== 1 ? 's' : ''}
        </span>

        <div
          style={{
            display: 'inline-flex',
            background: 'var(--ob-color-surface-secondary)',
            borderRadius: 'var(--ob-radius-pill)',
            padding: 'var(--ob-space-025)',
          }}
        >
          <button
            type="button"
            onClick={() => setViewMode('original')}
            style={{
              padding: 'var(--ob-space-035) var(--ob-space-085)',
              borderRadius: 'var(--ob-radius-pill)',
              border: 'none',
              background:
                viewMode === 'original'
                  ? 'var(--ob-color-surface-primary)'
                  : 'transparent',
              color:
                viewMode === 'original'
                  ? 'var(--ob-color-text-primary)'
                  : 'var(--ob-color-text-secondary)',
              fontSize: 'var(--ob-font-size-xs)',
              fontWeight: 'var(--ob-font-weight-medium)',
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
              padding: 'var(--ob-space-035) var(--ob-space-085)',
              borderRadius: 'var(--ob-radius-pill)',
              border: 'none',
              background:
                viewMode === 'marketing'
                  ? 'var(--ob-color-surface-primary)'
                  : 'transparent',
              color:
                viewMode === 'marketing'
                  ? 'var(--ob-color-text-primary)'
                  : 'var(--ob-color-text-secondary)',
              fontSize: 'var(--ob-font-size-xs)',
              fontWeight: 'var(--ob-font-weight-medium)',
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
          fontSize: 'var(--ob-font-size-xs)',
          color: 'var(--ob-color-text-secondary)',
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
          gap: 'var(--ob-space-075)',
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
                borderRadius: 'var(--ob-radius-sm)',
                overflow: 'hidden',
                background: 'var(--ob-color-surface-secondary)',
                cursor: 'pointer',
                opacity: isDeleting ? 0.5 : 1,
              }}
              onClick={() => setSelectedPhoto(photo)}
              onKeyDown={(e) => e.key === 'Enter' && setSelectedPhoto(photo)}
              role="button"
              tabIndex={0}
              aria-label={
                photo.notes || `Property photo ${photos.indexOf(photo) + 1}`
              }
            >
              {thumbnailUrl ? (
                <img
                  src={thumbnailUrl}
                  alt={photo.notes || 'Property photo'}
                  loading="lazy"
                  decoding="async"
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
                    color: 'var(--ob-color-text-secondary)',
                    fontSize: 'var(--ob-font-size-3xl)',
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
                    padding: 'var(--ob-space-025) var(--ob-space-050)',
                    background: 'linear-gradient(transparent, rgba(0,0,0,0.7))',
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: 'var(--ob-space-025)',
                  }}
                >
                  {photo.autoTags.slice(0, 2).map((tag) => (
                    <span
                      key={tag}
                      style={{
                        padding: 'var(--ob-space-025) var(--ob-space-035)',
                        background: 'rgba(255,255,255,0.2)',
                        borderRadius: 'var(--ob-radius-sm)',
                        fontSize: 'var(--ob-font-size-2xs)',
                        color: 'var(--ob-color-surface-primary)',
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
                    borderRadius: 'var(--ob-radius-pill)',
                    border: 'none',
                    background: 'rgba(0,0,0,0.6)',
                    color: 'var(--ob-color-surface-primary)',
                    fontSize: 'var(--ob-font-size-sm)',
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
          ref={lightboxRef}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.9)',
            zIndex: 1000,
            display: 'flex',
            flexDirection: 'column',
            padding: 'var(--ob-space-100)',
          }}
          onClick={() => setSelectedPhoto(null)}
          role="dialog"
          aria-modal="true"
          aria-label="Photo lightbox"
        >
          {/* Header */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: 'var(--ob-space-100)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ color: 'var(--ob-color-surface-primary)' }}>
              <div style={{ fontWeight: 'var(--ob-font-weight-semibold)' }}>
                {selectedPhoto.notes || 'Property Photo'}
              </div>
              {selectedPhoto.captureTimestamp && (
                <div
                  style={{
                    fontSize: 'var(--ob-font-size-xs)',
                    color: 'var(--ob-color-text-secondary)',
                  }}
                >
                  {new Date(selectedPhoto.captureTimestamp).toLocaleString()}
                </div>
              )}
            </div>

            <div style={{ display: 'flex', gap: 'var(--ob-space-050)' }}>
              {/* View toggle in lightbox */}
              <div
                style={{
                  display: 'inline-flex',
                  background: 'rgba(245, 235, 220, 0.1)',
                  borderRadius: 'var(--ob-radius-pill)',
                  padding: 'var(--ob-space-025)',
                }}
              >
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation()
                    setViewMode('original')
                  }}
                  style={{
                    padding: 'var(--ob-space-035) var(--ob-space-075)',
                    borderRadius: 'var(--ob-radius-pill)',
                    border: 'none',
                    background:
                      viewMode === 'original'
                        ? 'rgba(255,255,255,0.2)'
                        : 'transparent',
                    color: 'var(--ob-color-surface-primary)',
                    fontSize: 'var(--ob-font-size-xs)',
                    fontWeight: 'var(--ob-font-weight-medium)',
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
                    padding: 'var(--ob-space-035) var(--ob-space-075)',
                    borderRadius: 'var(--ob-radius-pill)',
                    border: 'none',
                    background:
                      viewMode === 'marketing'
                        ? 'rgba(255,255,255,0.2)'
                        : 'transparent',
                    color: 'var(--ob-color-surface-primary)',
                    fontSize: 'var(--ob-font-size-xs)',
                    fontWeight: 'var(--ob-font-weight-medium)',
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
                  padding: 'var(--ob-space-050) var(--ob-space-100)',
                  borderRadius: 'var(--ob-radius-sm)',
                  border: 'none',
                  background: 'rgba(245, 235, 220, 0.1)',
                  color: 'var(--ob-color-surface-primary)',
                  fontSize: 'var(--ob-font-size-sm)',
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
                loading="lazy"
                decoding="async"
                style={{
                  maxWidth: '100%',
                  maxHeight: '100%',
                  objectFit: 'contain',
                  borderRadius: 'var(--ob-radius-sm)',
                }}
              />
            ) : (
              <div style={{ color: 'var(--ob-color-text-secondary)' }}>
                Image not available
              </div>
            )}
          </div>

          {/* Footer with tags */}
          {selectedPhoto.autoTags.length > 0 && (
            <div
              style={{
                marginTop: 'var(--ob-space-100)',
                display: 'flex',
                flexWrap: 'wrap',
                gap: 'var(--ob-space-050)',
                justifyContent: 'center',
              }}
              onClick={(e) => e.stopPropagation()}
            >
              {selectedPhoto.autoTags.map((tag) => (
                <span
                  key={tag}
                  style={{
                    padding: 'var(--ob-space-025) var(--ob-space-075)',
                    background: 'rgba(245, 235, 220, 0.1)',
                    borderRadius: 'var(--ob-radius-pill)',
                    fontSize: 'var(--ob-font-size-xs)',
                    color: 'var(--ob-color-surface-primary)',
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
