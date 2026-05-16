/**
 * Voice Note List Component
 *
 * Displays previously uploaded voice notes for a property with playback controls.
 */

import { useState, useEffect, useCallback } from 'react'
import {
  fetchPropertyVoiceNotes,
  deleteVoiceNote,
  type PropertyVoiceNote,
} from '../../../../../api/siteAcquisition'

// ============================================================================
// Types
// ============================================================================

export interface VoiceNoteListProps {
  propertyId: string | null
  onVoiceNoteDeleted?: (voiceNoteId: string) => void
  refreshTrigger?: number
}

// ============================================================================
// Helper Functions
// ============================================================================

function formatDuration(seconds: number | null): string {
  if (seconds === null || seconds === 0) {
    return '0:00'
  }
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function formatDate(dateString: string | null): string {
  if (!dateString) {
    return 'Unknown date'
  }
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return 'Unknown date'
  }
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

// ============================================================================
// Component
// ============================================================================

export function VoiceNoteList({
  propertyId,
  onVoiceNoteDeleted,
  refreshTrigger = 0,
}: VoiceNoteListProps) {
  const [voiceNotes, setVoiceNotes] = useState<PropertyVoiceNote[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [expandedNoteId, setExpandedNoteId] = useState<string | null>(null)

  const loadVoiceNotes = useCallback(async () => {
    if (!propertyId) {
      setVoiceNotes([])
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const notes = await fetchPropertyVoiceNotes(propertyId)
      setVoiceNotes(notes)
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to load voice notes'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }, [propertyId])

  useEffect(() => {
    loadVoiceNotes()
  }, [loadVoiceNotes, refreshTrigger])

  const handleDelete = async (voiceNoteId: string) => {
    if (!propertyId) return

    const confirmed = window.confirm(
      'Are you sure you want to delete this voice note? This action cannot be undone.',
    )
    if (!confirmed) return

    setDeletingId(voiceNoteId)

    try {
      const success = await deleteVoiceNote(propertyId, voiceNoteId)
      if (success) {
        setVoiceNotes((prev) =>
          prev.filter((n) => n.voiceNoteId !== voiceNoteId),
        )
        onVoiceNoteDeleted?.(voiceNoteId)
      } else {
        setError('Failed to delete voice note')
      }
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to delete voice note'
      setError(message)
    } finally {
      setDeletingId(null)
    }
  }

  const toggleExpanded = (noteId: string) => {
    setExpandedNoteId((prev) => (prev === noteId ? null : noteId))
  }

  if (!propertyId) {
    return null
  }

  if (isLoading) {
    return (
      <div
        style={{
          background: 'var(--ob-color-surface-info, #f0f9ff)',
          borderRadius: 'var(--ob-radius-sm)',
          padding: 'var(--ob-space-150)',
          marginTop: 'var(--ob-space-150)',
        }}
      >
        <h4
          style={{
            margin: '0 0 var(--ob-space-100) 0',
            fontSize: 'var(--ob-font-size-base)',
            fontWeight: 'var(--ob-font-weight-semibold)',
            color: 'var(--ob-color-text-primary, #1d1d1f)',
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--ob-space-050)',
          }}
        >
          <span role="img" aria-label="headphones">
            🎧
          </span>
          Saved Voice Notes
        </h4>
        <p
          style={{
            margin: 0,
            fontSize: 'var(--ob-font-size-sm)',
            color: 'var(--ob-color-text-muted, #6b7280)',
          }}
        >
          Loading voice notes...
        </p>
      </div>
    )
  }

  if (voiceNotes.length === 0 && !error) {
    return null
  }

  return (
    <div
      style={{
        background: 'var(--ob-color-surface-info, #f0f9ff)',
        borderRadius: 'var(--ob-radius-sm)',
        padding: 'var(--ob-space-150)',
        marginTop: 'var(--ob-space-150)',
      }}
    >
      <h4
        style={{
          margin: '0 0 var(--ob-space-100) 0',
          fontSize: 'var(--ob-font-size-base)',
          fontWeight: 'var(--ob-font-weight-semibold)',
          color: 'var(--ob-color-text-primary, #1d1d1f)',
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--ob-space-050)',
        }}
      >
        <span role="img" aria-label="headphones">
          🎧
        </span>
        Saved Voice Notes ({voiceNotes.length})
      </h4>

      {error && (
        <div
          style={{
            padding: 'var(--ob-space-075)',
            background: 'var(--ob-color-surface-error, #fef2f2)',
            border: '1px solid var(--ob-color-border-error, #fecaca)',
            borderRadius: 'var(--ob-radius-sm)',
            color: 'var(--ob-color-status-error, #dc2626)',
            fontSize: 'var(--ob-font-size-sm)',
            marginBottom: 'var(--ob-space-100)',
          }}
        >
          {error}
        </div>
      )}

      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--ob-space-075)',
        }}
      >
        {voiceNotes.map((note) => (
          <div
            key={note.voiceNoteId}
            style={{
              background: 'white',
              border: '1px solid var(--ob-color-border-subtle, #e5e7eb)',
              borderRadius: 'var(--ob-radius-sm)',
              overflow: 'hidden',
            }}
          >
            {/* Main row */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--ob-space-075)',
                padding: 'var(--ob-space-075)',
              }}
            >
              {/* Audio player */}
              <audio
                controls
                src={note.publicUrl}
                style={{ height: 'var(--ob-space-200)', flex: '0 0 200px' }}
                preload="metadata"
              />

              {/* Title and metadata */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div
                  style={{
                    fontSize: 'var(--ob-font-size-sm)',
                    fontWeight: 'var(--ob-font-weight-medium)',
                    color: 'var(--ob-color-text-primary, #1d1d1f)',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                >
                  {note.title || note.filename || 'Voice Note'}
                </div>
                <div
                  style={{
                    fontSize: 'var(--ob-font-size-xs)',
                    color: 'var(--ob-color-text-muted, #6b7280)',
                    marginTop: '2px',
                  }}
                >
                  {formatDate(note.captureDate)}
                </div>
              </div>

              {/* Duration */}
              <span
                style={{
                  fontSize: 'var(--ob-font-size-sm-minus)',
                  color: 'var(--ob-color-text-muted, #6b7280)',
                  fontFamily: 'var(--ob-font-family-mono)',
                  whiteSpace: 'nowrap',
                }}
              >
                {formatDuration(note.durationSeconds)}
              </span>

              {/* Expand/collapse button */}
              <button
                type="button"
                onClick={() => toggleExpanded(note.voiceNoteId)}
                style={{
                  padding: 'var(--ob-space-025) var(--ob-space-050)',
                  borderRadius: 'var(--ob-radius-sm)',
                  border: '1px solid var(--ob-color-border-default, #d1d5db)',
                  background: 'white',
                  color: 'var(--ob-color-text-secondary, #374151)',
                  fontSize: 'var(--ob-font-size-xs)',
                  cursor: 'pointer',
                }}
                title={
                  expandedNoteId === note.voiceNoteId
                    ? 'Hide details'
                    : 'Show details'
                }
              >
                {expandedNoteId === note.voiceNoteId ? '▲' : '▼'}
              </button>

              {/* Delete button */}
              <button
                type="button"
                onClick={() => handleDelete(note.voiceNoteId)}
                disabled={deletingId === note.voiceNoteId}
                style={{
                  padding: 'var(--ob-space-025)',
                  borderRadius: 'var(--ob-radius-sm)',
                  border: 'none',
                  background: 'transparent',
                  color:
                    deletingId === note.voiceNoteId
                      ? 'var(--ob-color-border-default, #d1d5db)'
                      : 'var(--ob-color-status-error, #ef4444)',
                  cursor:
                    deletingId === note.voiceNoteId ? 'not-allowed' : 'pointer',
                  fontSize: 'var(--ob-font-size-base)',
                }}
                title="Delete voice note"
              >
                {deletingId === note.voiceNoteId ? '⏳' : '🗑️'}
              </button>
            </div>

            {/* Expanded details */}
            {expandedNoteId === note.voiceNoteId && (
              <div
                style={{
                  borderTop: '1px solid var(--ob-color-border-subtle, #e5e7eb)',
                  padding: 'var(--ob-space-075)',
                  background: 'var(--ob-color-bg-surface, #f9fafb)',
                  fontSize: 'var(--ob-font-size-sm-minus)',
                  color: 'var(--ob-color-text-secondary, #4b5563)',
                }}
              >
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'auto 1fr',
                    gap: 'var(--ob-space-050) var(--ob-space-100)',
                  }}
                >
                  <span style={{ fontWeight: 'var(--ob-font-weight-medium)' }}>
                    File:
                  </span>
                  <span>{note.filename}</span>

                  <span style={{ fontWeight: 'var(--ob-font-weight-medium)' }}>
                    Size:
                  </span>
                  <span>{formatFileSize(note.fileSize)}</span>

                  <span style={{ fontWeight: 'var(--ob-font-weight-medium)' }}>
                    Format:
                  </span>
                  <span>{note.mimeType}</span>

                  {note.location &&
                    (note.location.latitude || note.location.longitude) && (
                      <>
                        <span
                          style={{ fontWeight: 'var(--ob-font-weight-medium)' }}
                        >
                          Location:
                        </span>
                        <span>
                          {note.location.latitude?.toFixed(6)},{' '}
                          {note.location.longitude?.toFixed(6)}
                        </span>
                      </>
                    )}

                  {note.tags.length > 0 && (
                    <>
                      <span
                        style={{ fontWeight: 'var(--ob-font-weight-medium)' }}
                      >
                        Tags:
                      </span>
                      <span>{note.tags.join(', ')}</span>
                    </>
                  )}

                  {note.transcript && (
                    <>
                      <span
                        style={{ fontWeight: 'var(--ob-font-weight-medium)' }}
                      >
                        Transcript:
                      </span>
                      <span style={{ fontStyle: 'italic' }}>
                        {note.transcript}
                      </span>
                    </>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Refresh button */}
      <button
        type="button"
        onClick={loadVoiceNotes}
        disabled={isLoading}
        style={{
          marginTop: 'var(--ob-space-100)',
          padding: 'var(--ob-space-050) var(--ob-space-100)',
          borderRadius: 'var(--ob-radius-md)',
          border: '1px solid var(--ob-color-border-default, #d1d5db)',
          background: 'white',
          color: 'var(--ob-color-text-secondary, #374151)',
          fontSize: 'var(--ob-font-size-sm-minus)',
          cursor: isLoading ? 'not-allowed' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--ob-space-050)',
        }}
      >
        {isLoading ? '⏳ Refreshing...' : '🔄 Refresh'}
      </button>
    </div>
  )
}
