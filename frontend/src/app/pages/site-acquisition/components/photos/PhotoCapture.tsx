/**
 * PhotoCapture Component
 *
 * Allows users to upload photos for property documentation.
 * Supports file selection and camera capture on mobile devices.
 */

import { useCallback, useRef, useState } from 'react'
import type { PropertyPhase } from '../../../../../api/siteAcquisition'

export interface PhotoCaptureProps {
  propertyId: string
  phase: PropertyPhase
  onUpload: (
    file: File,
    options: { notes?: string; tags?: string[]; phase: PropertyPhase },
  ) => Promise<void>
  disabled?: boolean
}

export function PhotoCapture({
  propertyId: _propertyId,
  phase,
  onUpload,
  disabled = false,
}: PhotoCaptureProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const [notes, setNotes] = useState('')

  const handleFileChange = useCallback(
    async (files: FileList | null) => {
      if (!files || files.length === 0) return

      setIsUploading(true)
      try {
        for (let i = 0; i < files.length; i++) {
          const file = files[i]
          if (file.type.startsWith('image/')) {
            await onUpload(file, {
              notes: notes.trim() || undefined,
              phase,
            })
          }
        }
        setNotes('')
      } finally {
        setIsUploading(false)
        if (fileInputRef.current) {
          fileInputRef.current.value = ''
        }
      }
    },
    [notes, phase, onUpload],
  )

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      handleFileChange(e.target.files)
    },
    [handleFileChange],
  )

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      setDragActive(false)
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        handleFileChange(e.dataTransfer.files)
      }
    },
    [handleFileChange],
  )

  const handleClick = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--ob-space-200)',
      }}
    >
      {/* Notes input */}
      <div>
        <label
          htmlFor="photo-notes"
          style={{
            display: 'block',
            fontSize: '0.8125rem',
            fontWeight: 600,
            color: 'var(--ob-color-text-primary)',
            marginBottom: 'var(--ob-space-50)',
          }}
        >
          Photo Notes (optional)
        </label>
        <input
          id="photo-notes"
          type="text"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Add notes about this photo..."
          disabled={disabled || isUploading}
          style={{
            width: '100%',
            padding: 'var(--ob-space-100) 0.75rem',
            borderRadius: 'var(--ob-radius-md)',
            border: '1px solid var(--ob-color-border-default)',
            fontSize: '0.875rem',
            outline: 'none',
          }}
        />
      </div>

      {/* Drop zone */}
      <div
        role="button"
        tabIndex={0}
        onClick={handleClick}
        onKeyDown={(e) => e.key === 'Enter' && handleClick()}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        style={{
          border: `2px dashed ${dragActive ? '#3b82f6' : 'var(--ob-color-border-default)'}`,
          borderRadius: 'var(--ob-radius-sm)',
          padding: 'var(--ob-space-400)',
          textAlign: 'center',
          background: dragActive
            ? '#eff6ff'
            : disabled
              ? '#f9fafb'
              : 'var(--ob-color-bg-default)',
          cursor: disabled || isUploading ? 'not-allowed' : 'pointer',
          transition: 'all 0.2s ease',
          opacity: disabled ? 0.6 : 1,
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          multiple
          capture="environment"
          onChange={handleInputChange}
          disabled={disabled || isUploading}
          style={{ display: 'none' }}
        />

        {isUploading ? (
          <div style={{ color: 'var(--ob-color-text-secondary)' }}>
            <div
              style={{
                width: '40px',
                height: '40px',
                margin: '0 auto 0.75rem',
                border: '3px solid var(--ob-color-border-subtle)',
                borderTop: '3px solid var(--ob-color-primary)',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite',
              }}
            />
            <p style={{ margin: 0, fontWeight: 500 }}>Uploading...</p>
          </div>
        ) : (
          <>
            <div
              style={{
                fontSize: '2.5rem',
                marginBottom: 'var(--ob-space-100)',
              }}
            >
              {'\uD83D\uDCF7'}
            </div>
            <p
              style={{
                margin: '0 0 0.25rem',
                fontSize: '0.9375rem',
                fontWeight: 600,
                color: 'var(--ob-color-text-primary)',
              }}
            >
              {dragActive ? 'Drop photos here' : 'Upload Photos'}
            </p>
            <p
              style={{
                margin: 0,
                fontSize: '0.8125rem',
                color: 'var(--ob-color-text-secondary)',
              }}
            >
              Drag and drop or click to select
            </p>
            <p
              style={{
                margin: 'var(--ob-space-100) 0 0',
                fontSize: '0.75rem',
                color: 'var(--ob-color-text-tertiary)',
              }}
            >
              Photos will be watermarked for{' '}
              {phase === 'acquisition' ? 'Acquisition' : 'Sales'} phase
            </p>
          </>
        )}
      </div>

      <style>
        {`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}
      </style>
    </div>
  )
}
