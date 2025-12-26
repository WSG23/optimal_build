/**
 * Voice Note Recorder Component
 *
 * Provides audio recording functionality for site documentation.
 * Uses the Web Audio API and MediaRecorder for capturing voice notes.
 */

import { useState, useRef, useCallback, useEffect } from 'react'

// ============================================================================
// Types
// ============================================================================

export interface VoiceNote {
  id: string
  blob: Blob
  duration: number
  title: string
  timestamp: Date
  uploaded?: boolean
}

export interface VoiceNoteRecorderProps {
  propertyId: string | null
  onVoiceNoteRecorded?: (note: VoiceNote) => void
  onUploadComplete?: (response: VoiceNoteUploadResponse) => void
  latitude?: number
  longitude?: number
  disabled?: boolean
}

interface VoiceNoteUploadResponse {
  voice_note_id: string
  property_id: string
  storage_key: string
  public_url: string
  duration_seconds: number | null
  title: string | null
}

// ============================================================================
// Hooks
// ============================================================================

function useVoiceRecorder() {
  const [isRecording, setIsRecording] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [duration, setDuration] = useState(0)
  const [audioLevel, setAudioLevel] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const startTimeRef = useRef<number>(0)
  const durationIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const animationFrameRef = useRef<number | null>(null)

  const cleanup = useCallback(() => {
    if (durationIntervalRef.current) {
      clearInterval(durationIntervalRef.current)
      durationIntervalRef.current = null
    }
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current)
      animationFrameRef.current = null
    }
    if (mediaRecorderRef.current?.stream) {
      mediaRecorderRef.current.stream
        .getTracks()
        .forEach((track) => track.stop())
    }
    mediaRecorderRef.current = null
    analyserRef.current = null
    setAudioLevel(0)
  }, [])

  const startRecording = useCallback(async () => {
    try {
      setError(null)
      audioChunksRef.current = []

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

      // Set up audio analysis for visual feedback
      const audioContext = new AudioContext()
      const source = audioContext.createMediaStreamSource(stream)
      const analyser = audioContext.createAnalyser()
      analyser.fftSize = 256
      source.connect(analyser)
      analyserRef.current = analyser

      // Create MediaRecorder with webm format (widely supported)
      const options = { mimeType: 'audio/webm' }
      const mediaRecorder = new MediaRecorder(stream, options)

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorderRef.current = mediaRecorder
      mediaRecorder.start(100) // Collect data every 100ms

      startTimeRef.current = Date.now()
      setIsRecording(true)
      setIsPaused(false)
      setDuration(0)

      // Update duration every 100ms
      durationIntervalRef.current = setInterval(() => {
        setDuration(Math.floor((Date.now() - startTimeRef.current) / 1000))
      }, 100)

      // Audio level visualization
      const updateAudioLevel = () => {
        if (analyserRef.current && isRecording) {
          const dataArray = new Uint8Array(
            analyserRef.current.frequencyBinCount,
          )
          analyserRef.current.getByteFrequencyData(dataArray)
          const average = dataArray.reduce((a, b) => a + b) / dataArray.length
          setAudioLevel(average / 255) // Normalize to 0-1
          animationFrameRef.current = requestAnimationFrame(updateAudioLevel)
        }
      }
      updateAudioLevel()
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to start recording'
      setError(message)
      console.error('Recording error:', err)
    }
  }, [isRecording])

  const stopRecording = useCallback((): Promise<Blob | null> => {
    return new Promise((resolve) => {
      if (!mediaRecorderRef.current || !isRecording) {
        resolve(null)
        return
      }

      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, {
          type: 'audio/webm',
        })
        cleanup()
        setIsRecording(false)
        setIsPaused(false)
        resolve(audioBlob)
      }

      mediaRecorderRef.current.stop()
    })
  }, [isRecording, cleanup])

  const pauseRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording && !isPaused) {
      mediaRecorderRef.current.pause()
      setIsPaused(true)
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current)
      }
    }
  }, [isRecording, isPaused])

  const resumeRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording && isPaused) {
      mediaRecorderRef.current.resume()
      setIsPaused(false)
      durationIntervalRef.current = setInterval(() => {
        setDuration(Math.floor((Date.now() - startTimeRef.current) / 1000))
      }, 100)
    }
  }, [isRecording, isPaused])

  useEffect(() => {
    return cleanup
  }, [cleanup])

  return {
    isRecording,
    isPaused,
    duration,
    audioLevel,
    error,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
  }
}

// ============================================================================
// Helper Functions
// ============================================================================

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// ============================================================================
// Component
// ============================================================================

export function VoiceNoteRecorder({
  propertyId,
  onVoiceNoteRecorded,
  onUploadComplete,
  latitude,
  longitude,
  disabled = false,
}: VoiceNoteRecorderProps) {
  const {
    isRecording,
    isPaused,
    duration,
    audioLevel,
    error: recordingError,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
  } = useVoiceRecorder()

  const [voiceNotes, setVoiceNotes] = useState<VoiceNote[]>([])
  const [editingNoteId, setEditingNoteId] = useState<string | null>(null)
  const [editTitle, setEditTitle] = useState('')
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)

  const handleStartRecording = async () => {
    await startRecording()
  }

  const handleStopRecording = async () => {
    const blob = await stopRecording()
    if (blob) {
      const note: VoiceNote = {
        id: `local-${Date.now()}`,
        blob,
        duration,
        title: `Voice Note ${voiceNotes.length + 1}`,
        timestamp: new Date(),
      }
      setVoiceNotes((prev) => [...prev, note])
      onVoiceNoteRecorded?.(note)
    }
  }

  const handleDeleteNote = (noteId: string) => {
    setVoiceNotes((prev) => prev.filter((n) => n.id !== noteId))
  }

  const handleEditNote = (note: VoiceNote) => {
    setEditingNoteId(note.id)
    setEditTitle(note.title)
  }

  const handleSaveEdit = (noteId: string) => {
    setVoiceNotes((prev) =>
      prev.map((n) => (n.id === noteId ? { ...n, title: editTitle } : n)),
    )
    setEditingNoteId(null)
    setEditTitle('')
  }

  const handleUploadNote = async (note: VoiceNote) => {
    if (!propertyId) {
      setUploadError('Property must be captured before uploading voice notes')
      return
    }

    setIsUploading(true)
    setUploadError(null)

    try {
      const formData = new FormData()
      formData.append(
        'file',
        note.blob,
        `${note.title.replace(/\s+/g, '_')}.webm`,
      )
      formData.append('duration_seconds', note.duration.toString())
      formData.append('title', note.title)

      if (latitude !== undefined && longitude !== undefined) {
        formData.append('latitude', latitude.toString())
        formData.append('longitude', longitude.toString())
      }

      const response = await fetch(
        `/api/v1/agents/commercial-property/properties/${propertyId}/voice-notes`,
        {
          method: 'POST',
          body: formData,
        },
      )

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Upload failed')
      }

      const result: VoiceNoteUploadResponse = await response.json()

      // Mark note as uploaded
      setVoiceNotes((prev) =>
        prev.map((n) => (n.id === note.id ? { ...n, uploaded: true } : n)),
      )

      onUploadComplete?.(result)
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to upload voice note'
      setUploadError(message)
    } finally {
      setIsUploading(false)
    }
  }

  const canRecord = !disabled && !isRecording

  return (
    <div
      style={{
        background: 'var(--ob-color-bg-surface-elevated)',
        borderRadius: 'var(--ob-radius-sm)',
        padding: '1.25rem',
        marginTop: '1.5rem',
      }}
    >
      <h4
        style={{
          margin: '0 0 1rem 0',
          fontSize: '1rem',
          fontWeight: 600,
          color: 'var(--ob-color-text-primary)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
        }}
      >
        <span role="img" aria-label="microphone">
          🎙️
        </span>
        Voice Notes
      </h4>

      {/* Recording Controls */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '1rem',
          marginBottom: '1rem',
        }}
      >
        {!isRecording ? (
          <button
            type="button"
            onClick={handleStartRecording}
            disabled={!canRecord}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.75rem 1.25rem',
              borderRadius: 'var(--ob-radius-sm)',
              border: 'none',
              background: canRecord
                ? 'var(--ob-color-status-error-text)'
                : 'var(--ob-color-border-subtle)',
              color: 'white',
              fontSize: '0.9rem',
              fontWeight: 500,
              cursor: canRecord ? 'pointer' : 'not-allowed',
              transition: 'background 0.2s',
            }}
          >
            <span
              style={{
                width: '12px',
                height: '12px',
                borderRadius: 'var(--ob-radius-pill)',
                background: 'white',
              }}
            />
            Start Recording
          </button>
        ) : (
          <>
            <button
              type="button"
              onClick={isPaused ? resumeRecording : pauseRecording}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.75rem 1rem',
                borderRadius: 'var(--ob-radius-sm)',
                border: '1px solid var(--ob-color-border-subtle)',
                background: 'white',
                color: 'var(--ob-color-text-secondary)',
                fontSize: '0.9rem',
                fontWeight: 500,
                cursor: 'pointer',
              }}
            >
              {isPaused ? '▶ Resume' : '⏸ Pause'}
            </button>

            <button
              type="button"
              onClick={handleStopRecording}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.75rem 1rem',
                borderRadius: 'var(--ob-radius-sm)',
                border: 'none',
                background: 'var(--ob-color-text-primary)',
                color: 'white',
                fontSize: '0.9rem',
                fontWeight: 500,
                cursor: 'pointer',
              }}
            >
              ⏹ Stop
            </button>

            {/* Recording indicator */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
              }}
            >
              <div
                style={{
                  width: '10px',
                  height: '10px',
                  borderRadius: 'var(--ob-radius-pill)',
                  background: isPaused
                    ? 'var(--ob-warning-500)'
                    : 'var(--ob-color-status-error-text)',
                  animation: isPaused ? 'none' : 'pulse 1s infinite',
                }}
              />
              <span
                style={{
                  fontFamily: 'ui-monospace, monospace',
                  fontSize: '1.1rem',
                  fontWeight: 600,
                  color: 'var(--ob-color-text-primary)',
                }}
              >
                {formatDuration(duration)}
              </span>

              {/* Audio level meter */}
              <div
                style={{
                  width: '60px',
                  height: '8px',
                  background: 'var(--ob-color-border-subtle)',
                  borderRadius: 'var(--ob-radius-sm)',
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    width: `${audioLevel * 100}%`,
                    height: '100%',
                    background:
                      audioLevel > 0.7
                        ? 'var(--ob-color-status-error-text)'
                        : 'var(--ob-color-status-success-text)',
                    transition: 'width 0.1s',
                  }}
                />
              </div>
            </div>
          </>
        )}
      </div>

      {/* Error messages */}
      {(recordingError || uploadError) && (
        <div
          style={{
            padding: '0.75rem',
            background: 'var(--ob-error-50)',
            border: '1px solid var(--ob-error-200)',
            borderRadius: 'var(--ob-radius-sm)',
            color: 'var(--ob-color-status-error-text)',
            fontSize: '0.875rem',
            marginBottom: '1rem',
          }}
        >
          {recordingError || uploadError}
        </div>
      )}

      {/* Recorded Notes List */}
      {voiceNotes.length > 0 && (
        <div style={{ marginTop: '1rem' }}>
          <h5
            style={{
              margin: '0 0 0.75rem 0',
              fontSize: '0.9rem',
              fontWeight: 500,
              color: 'var(--ob-color-text-muted)',
            }}
          >
            Recorded Notes ({voiceNotes.length})
          </h5>

          <div
            style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}
          >
            {voiceNotes.map((note) => (
              <div
                key={note.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  padding: '0.75rem',
                  background: 'white',
                  border: '1px solid var(--ob-color-border-subtle)',
                  borderRadius: 'var(--ob-radius-sm)',
                }}
              >
                {/* Play button / Audio element */}
                <audio
                  controls
                  src={URL.createObjectURL(note.blob)}
                  style={{ height: 'var(--ob-space-400)', flex: '0 0 200px' }}
                />

                {/* Title (editable) */}
                {editingNoteId === note.id ? (
                  <input
                    type="text"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleSaveEdit(note.id)
                      if (e.key === 'Escape') setEditingNoteId(null)
                    }}
                    style={{
                      flex: 1,
                      padding: '0.375rem 0.5rem',
                      border: '1px solid var(--ob-color-border-subtle)',
                      borderRadius: 'var(--ob-radius-sm)',
                      fontSize: '0.875rem',
                    }}
                    autoFocus
                  />
                ) : (
                  <span
                    style={{
                      flex: 1,
                      fontSize: '0.875rem',
                      color: 'var(--ob-color-text-primary)',
                      cursor: 'pointer',
                    }}
                    onClick={() => handleEditNote(note)}
                    title="Click to edit title"
                  >
                    {note.title}
                  </span>
                )}

                {/* Duration */}
                <span
                  style={{
                    fontSize: '0.8rem',
                    color: 'var(--ob-color-text-muted)',
                    fontFamily: 'ui-monospace, monospace',
                  }}
                >
                  {formatDuration(note.duration)}
                </span>

                {/* Status / Actions */}
                {note.uploaded ? (
                  <span
                    style={{
                      fontSize: '0.8rem',
                      color: 'var(--ob-color-status-success-text)',
                      fontWeight: 500,
                    }}
                  >
                    ✓ Uploaded
                  </span>
                ) : (
                  <button
                    type="button"
                    onClick={() => handleUploadNote(note)}
                    disabled={isUploading || !propertyId}
                    style={{
                      padding: '0.375rem 0.75rem',
                      borderRadius: 'var(--ob-radius-md)',
                      border: 'none',
                      background: propertyId
                        ? 'var(--ob-color-brand-primary)'
                        : 'var(--ob-color-border-subtle)',
                      color: 'white',
                      fontSize: '0.8rem',
                      fontWeight: 500,
                      cursor: propertyId ? 'pointer' : 'not-allowed',
                    }}
                    title={
                      !propertyId
                        ? 'Capture property first'
                        : 'Upload to server'
                    }
                  >
                    {isUploading ? 'Uploading...' : 'Upload'}
                  </button>
                )}

                {/* Delete button */}
                <button
                  type="button"
                  onClick={() => handleDeleteNote(note.id)}
                  style={{
                    padding: '0.375rem',
                    borderRadius: 'var(--ob-radius-sm)',
                    border: 'none',
                    background: 'transparent',
                    color: 'var(--ob-color-text-muted)',
                    cursor: 'pointer',
                    fontSize: '1rem',
                  }}
                  title="Delete note"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Instructions when no property captured */}
      {!propertyId && voiceNotes.length > 0 && (
        <p
          style={{
            margin: '0.75rem 0 0 0',
            fontSize: '0.8rem',
            color: 'var(--ob-color-text-muted)',
            fontStyle: 'italic',
          }}
        >
          Capture a property to upload voice notes to the server.
        </p>
      )}

      {/* CSS for pulse animation */}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  )
}
