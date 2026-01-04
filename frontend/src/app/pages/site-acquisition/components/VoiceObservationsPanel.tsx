/**
 * Voice Observations Panel Component
 *
 * Sidebar panel for voice note recording and management.
 * Displays in a compact format suitable for sidebar placement.
 *
 * Design Principles:
 * - Square Cyber-Minimalism: 4px radius cards, 2px radius buttons
 * - Functional Color Language: Red for recording state
 * - Progressive Disclosure: Expandable note details
 */

import { useState, useRef, useCallback, useEffect } from 'react'
import { Mic, Stop, Delete } from '@mui/icons-material'

// ============================================================================
// Types
// ============================================================================

export interface VoiceRecording {
  id: string
  blob: Blob
  duration: number
  title: string
  timestamp: Date
  uploaded?: boolean
}

export interface VoiceObservationsPanelProps {
  /** Property ID for uploading (null if no property captured) */
  propertyId: string | null
  /** Latitude for geotagging */
  latitude?: number
  /** Longitude for geotagging */
  longitude?: number
  /** Whether recording is disabled */
  disabled?: boolean
  /** Callback when a recording is uploaded */
  onUploadComplete?: () => void
}

// ============================================================================
// Helper Functions
// ============================================================================

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function formatDate(date: Date): string {
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// ============================================================================
// Component
// ============================================================================

export function VoiceObservationsPanel({
  propertyId,
  latitude,
  longitude,
  disabled = false,
  onUploadComplete,
}: VoiceObservationsPanelProps) {
  const [isRecording, setIsRecording] = useState(false)
  const [duration, setDuration] = useState(0)
  const [recordings, setRecordings] = useState<VoiceRecording[]>([])
  const [error, setError] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState(false)

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const startTimeRef = useRef<number>(0)
  const durationIntervalRef = useRef<NodeJS.Timeout | null>(null)

  const cleanup = useCallback(() => {
    if (durationIntervalRef.current) {
      clearInterval(durationIntervalRef.current)
      durationIntervalRef.current = null
    }
    if (mediaRecorderRef.current?.stream) {
      mediaRecorderRef.current.stream
        .getTracks()
        .forEach((track) => track.stop())
    }
    mediaRecorderRef.current = null
  }, [])

  useEffect(() => {
    return cleanup
  }, [cleanup])

  const startRecording = useCallback(async () => {
    try {
      setError(null)
      audioChunksRef.current = []

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm',
      })

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorderRef.current = mediaRecorder
      mediaRecorder.start(100)

      startTimeRef.current = Date.now()
      setIsRecording(true)
      setDuration(0)

      durationIntervalRef.current = setInterval(() => {
        setDuration(Math.floor((Date.now() - startTimeRef.current) / 1000))
      }, 100)
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to start recording'
      setError(message)
    }
  }, [])

  const stopRecording = useCallback(() => {
    if (!mediaRecorderRef.current || !isRecording) return

    mediaRecorderRef.current.onstop = () => {
      const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
      const recording: VoiceRecording = {
        id: `vn-${Date.now()}`,
        blob,
        duration,
        title: `VN_${new Date().toISOString().slice(5, 10).replace('-', '')}_${String(recordings.length + 1).padStart(2, '0')}.webm`,
        timestamp: new Date(),
      }
      setRecordings((prev) => [...prev, recording])
      cleanup()
      setIsRecording(false)
    }

    mediaRecorderRef.current.stop()
  }, [isRecording, duration, recordings.length, cleanup])

  const deleteRecording = useCallback((id: string) => {
    setRecordings((prev) => prev.filter((r) => r.id !== id))
  }, [])

  const uploadRecording = useCallback(
    async (recording: VoiceRecording) => {
      if (!propertyId) {
        setError('Capture a property first to upload voice notes')
        return
      }

      setIsUploading(true)
      setError(null)

      try {
        const formData = new FormData()
        formData.append('file', recording.blob, recording.title)
        formData.append('duration_seconds', recording.duration.toString())
        formData.append('title', recording.title)

        if (latitude !== undefined && longitude !== undefined) {
          formData.append('latitude', latitude.toString())
          formData.append('longitude', longitude.toString())
        }

        const response = await fetch(
          `/api/v1/agents/commercial-property/properties/${propertyId}/voice-notes`,
          { method: 'POST', body: formData },
        )

        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.detail || 'Upload failed')
        }

        setRecordings((prev) =>
          prev.map((r) =>
            r.id === recording.id ? { ...r, uploaded: true } : r,
          ),
        )
        onUploadComplete?.()
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to upload'
        setError(message)
      } finally {
        setIsUploading(false)
      }
    },
    [propertyId, latitude, longitude, onUploadComplete],
  )

  const canRecord = !disabled && !isRecording

  return (
    <div className="voice-observations-panel">
      {/* Header */}
      <div className="voice-observations-panel__header">
        <Mic sx={{ fontSize: 20, color: 'var(--ob-color-text-secondary)' }} />
        <span className="voice-observations-panel__title">
          Voice Observations
        </span>
      </div>

      {/* Capture Sequence Module - Machined Edge Style */}
      <div className="voice-capture-module">
        <div className="voice-capture-module__header">
          <span className="voice-capture-module__label">CAPTURE SEQUENCE</span>
          <span
            className={`voice-capture-module__status voice-capture-module__status--${isRecording ? 'active' : 'idle'}`}
          >
            <span className="voice-capture-module__status-dot" />
            {isRecording ? 'RECORDING' : 'STANDBY'}
          </span>
        </div>

        <button
          type="button"
          onClick={isRecording ? stopRecording : startRecording}
          disabled={!canRecord && !isRecording}
          className={`voice-capture-module__trigger ${isRecording ? 'voice-capture-module__trigger--active' : ''}`}
          aria-label={isRecording ? 'Stop recording' : 'Start recording'}
        >
          <div className="voice-capture-module__trigger-icon">
            {isRecording ? (
              <Stop sx={{ fontSize: 24 }} />
            ) : (
              <Mic sx={{ fontSize: 24 }} />
            )}
          </div>
          <div className="voice-capture-module__trigger-text">
            {isRecording ? 'TERMINATE' : 'INITIATE'}
          </div>
        </button>

        {isRecording && (
          <div className="voice-capture-module__telemetry">
            <span className="voice-capture-module__duration">
              {formatDuration(duration)}
            </span>
            <span className="voice-capture-module__duration-label">
              ELAPSED
            </span>
          </div>
        )}
      </div>

      {/* Error */}
      {error && <div className="voice-observations-panel__error">{error}</div>}

      {/* Recordings List */}
      {recordings.length > 0 && (
        <div className="voice-observations-panel__list">
          <div className="voice-observations-panel__list-header">
            Recorded ({recordings.length})
          </div>
          {recordings.map((recording) => (
            <div key={recording.id} className="voice-observations-panel__item">
              <div className="voice-observations-panel__item-icon">
                <Mic sx={{ fontSize: 16 }} />
              </div>
              <div className="voice-observations-panel__item-info">
                <div className="voice-observations-panel__item-name">
                  {recording.title}
                </div>
                <div className="voice-observations-panel__item-meta">
                  {formatDate(recording.timestamp)} •{' '}
                  {formatDuration(recording.duration)}
                </div>
              </div>
              {recording.uploaded ? (
                <span className="voice-observations-panel__uploaded-badge">
                  ✓
                </span>
              ) : (
                <button
                  type="button"
                  onClick={() => uploadRecording(recording)}
                  disabled={isUploading || !propertyId}
                  className="voice-observations-panel__upload-btn"
                >
                  {isUploading ? '...' : 'Upload'}
                </button>
              )}
              <button
                type="button"
                onClick={() => deleteRecording(recording.id)}
                className="voice-observations-panel__delete-btn"
                aria-label="Delete recording"
              >
                <Delete sx={{ fontSize: 16 }} />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Instructions */}
      {!propertyId && recordings.length > 0 && (
        <div className="voice-observations-panel__instructions">
          Capture a property to upload recordings
        </div>
      )}
    </div>
  )
}
