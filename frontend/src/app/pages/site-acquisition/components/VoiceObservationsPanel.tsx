/**
 * Voice Notes Panel Component
 *
 * Sidebar panel for recording voice notes, uploading them to a property,
 * and surfacing saved transcripts when available.
 */

import { useState, useRef, useCallback, useEffect } from 'react'
import Mic from '@mui/icons-material/Mic'
import Stop from '@mui/icons-material/Stop'
import Delete from '@mui/icons-material/Delete'
import {
  fetchPropertyVoiceNotes,
  type PropertyVoiceNote,
} from '../../../../api/siteAcquisition'

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

function formatDuration(seconds: number | null): string {
  if (seconds == null || Number.isNaN(seconds)) {
    return '0:00'
  }
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function formatDate(date: Date | string | null): string {
  if (!date) {
    return 'Unknown date'
  }

  const parsed = typeof date === 'string' ? new Date(date) : date
  if (Number.isNaN(parsed.getTime())) {
    return 'Unknown date'
  }

  return parsed.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

async function readUploadErrorMessage(response: Response): Promise<string> {
  const jsonResponse = response.clone()
  try {
    const payload = await jsonResponse.json()
    if (typeof payload?.detail === 'string' && payload.detail.trim()) {
      return payload.detail.trim()
    }
    if (typeof payload?.message === 'string' && payload.message.trim()) {
      return payload.message.trim()
    }
  } catch {
    // Fall through to text parsing.
  }

  try {
    const text = await response.text()
    if (text.trim()) {
      return text.trim()
    }
  } catch {
    // Ignore text parsing failures and use status fallback below.
  }

  return response.status
    ? `Upload failed (${response.status})`
    : 'Upload failed'
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
  const [savedNotes, setSavedNotes] = useState<PropertyVoiceNote[]>([])
  const [error, setError] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [isLoadingSavedNotes, setIsLoadingSavedNotes] = useState(false)

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

  const loadSavedNotes = useCallback(async () => {
    if (!propertyId) {
      setSavedNotes([])
      return
    }

    setIsLoadingSavedNotes(true)
    try {
      const notes = await fetchPropertyVoiceNotes(propertyId)
      setSavedNotes(notes)
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to load voice notes'
      setError(message)
    } finally {
      setIsLoadingSavedNotes(false)
    }
  }, [propertyId])

  useEffect(() => {
    void loadSavedNotes()
  }, [loadSavedNotes])

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
          throw new Error(await readUploadErrorMessage(response))
        }

        setRecordings((prev) => prev.filter((r) => r.id !== recording.id))
        await loadSavedNotes()
        onUploadComplete?.()
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to upload'
        setError(message)
      } finally {
        setIsUploading(false)
      }
    },
    [propertyId, latitude, longitude, onUploadComplete, loadSavedNotes],
  )

  const canRecord = !disabled && !isRecording

  return (
    <div className="voice-observations-panel">
      <button
        type="button"
        onClick={isRecording ? stopRecording : startRecording}
        disabled={!canRecord && !isRecording}
        className={`voice-observations-panel__primary-btn ${isRecording ? 'voice-observations-panel__primary-btn--active' : ''}`}
        aria-label={
          isRecording ? 'Stop recording voice note' : 'Record voice note'
        }
        title="Site notes. Transcripts appear after upload."
      >
        <span className="voice-observations-panel__primary-btn-icon">
          {isRecording ? (
            <Stop sx={{ fontSize: 24 }} />
          ) : (
            <Mic sx={{ fontSize: 24 }} />
          )}
        </span>
        <span className="voice-observations-panel__primary-btn-text">
          {isRecording ? 'Stop Recording' : 'Voice Record'}
        </span>
      </button>

      {isRecording && (
        <div className="voice-observations-panel__telemetry">
          <span className="voice-observations-panel__duration">
            {formatDuration(duration)}
          </span>
          <span className="voice-observations-panel__duration-label">
            elapsed
          </span>
        </div>
      )}

      {/* Error */}
      {error && <div className="voice-observations-panel__error">{error}</div>}

      {/* Local recordings awaiting upload */}
      {recordings.length > 0 && (
        <div className="voice-observations-panel__list">
          <div className="voice-observations-panel__list-header">
            Pending Uploads ({recordings.length})
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
              <button
                type="button"
                onClick={() => uploadRecording(recording)}
                disabled={isUploading || !propertyId}
                className="voice-observations-panel__upload-btn"
              >
                {isUploading ? 'Uploading…' : 'Upload'}
              </button>
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

      {/* Saved notes and transcripts */}
      {propertyId && (isLoadingSavedNotes || savedNotes.length > 0) && (
        <div className="voice-observations-panel__list voice-observations-panel__list--saved">
          <div className="voice-observations-panel__list-header voice-observations-panel__list-header--with-action">
            <span>Saved Notes ({savedNotes.length})</span>
            <button
              type="button"
              onClick={() => void loadSavedNotes()}
              className="voice-observations-panel__refresh-btn"
              disabled={isLoadingSavedNotes}
            >
              {isLoadingSavedNotes ? 'Refreshing…' : 'Refresh'}
            </button>
          </div>

          {savedNotes.map((note) => (
            <div
              key={note.voiceNoteId}
              className="voice-observations-panel__saved-item"
            >
              <div className="voice-observations-panel__saved-header">
                <div className="voice-observations-panel__saved-info">
                  <div className="voice-observations-panel__saved-title">
                    {note.title || note.filename || 'Voice Note'}
                  </div>
                  <div className="voice-observations-panel__saved-meta">
                    {formatDate(note.captureDate)} •{' '}
                    {formatDuration(note.durationSeconds)}
                  </div>
                </div>
                <audio
                  controls
                  preload="metadata"
                  src={note.publicUrl}
                  className="voice-observations-panel__audio"
                />
              </div>

              <div className="voice-observations-panel__transcript-block">
                <div className="voice-observations-panel__transcript-label">
                  Transcript
                </div>
                <div className="voice-observations-panel__transcript-copy">
                  {note.transcript?.trim() || 'Transcript pending.'}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {!propertyId && recordings.length > 0 && (
        <div className="voice-observations-panel__instructions">
          Capture a property to upload recordings
        </div>
      )}
    </div>
  )
}
