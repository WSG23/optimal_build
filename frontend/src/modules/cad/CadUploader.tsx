import { ChangeEvent, DragEvent, useRef, useState } from 'react'

import type { ParseStatusUpdate } from '../../api/client'
import { useTranslation } from '../../i18n'

interface CadUploaderProps {
  onUpload: (file: File) => void
  isUploading?: boolean
  status?: ParseStatusUpdate | null
  zoneCode?: string | null
}

export function CadUploader({ onUpload, isUploading = false, status, zoneCode }: CadUploaderProps) {
  const { t } = useTranslation()
  const inputRef = useRef<HTMLInputElement | null>(null)
  const [isDragging, setIsDragging] = useState(false)

  const handleFiles = (files: FileList | null) => {
    if (!files || files.length === 0) {
      return
    }
    onUpload(files[0])
  }

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsDragging(false)
    handleFiles(event.dataTransfer?.files ?? null)
  }

  const handleDragOver = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsDragging(false)
  }

  const handleBrowse = () => {
    inputRef.current?.click()
  }

  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    handleFiles(event.target.files)
  }

  const latestStatus = status?.status === 'ready'
    ? t('uploader.ready')
    : status?.status === 'error'
      ? t('uploader.error')
      : status
        ? t('uploader.parsing')
        : null

  const fallbackDash = t('common.fallback.dash')

  return (
    <div className="cad-uploader">
      <div
        className={`cad-uploader__dropzone${isDragging ? ' cad-uploader__dropzone--dragging' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        role="presentation"
      >
        <input
          ref={inputRef}
          type="file"
          accept=".dxf,.dwg,.zip"
          className="cad-uploader__input"
          onChange={handleChange}
          disabled={isUploading}
        />
        <p className="cad-uploader__hint">{t('uploader.dropHint')}</p>
        <button type="button" className="cad-uploader__browse" onClick={handleBrowse} disabled={isUploading}>
          {t('uploader.browseLabel')}
        </button>
      </div>

      <aside className="cad-uploader__status">
        <h3>{t('uploader.latestStatus')}</h3>
        {latestStatus ? <p>{latestStatus}</p> : <p>{t('uploader.parsing')}</p>}
        {status?.message && <p className="cad-uploader__message">{status.message}</p>}
        <dl className="cad-uploader__meta">
          <div>
            <dt>{t('uploader.zone')}</dt>
            <dd>{zoneCode ?? status?.zoneCode ?? fallbackDash}</dd>
          </div>
          <div>
            <dt>{t('uploader.overlays')}</dt>
            <dd>{status?.overlays?.length ? status.overlays.join(', ') : fallbackDash}</dd>
          </div>
          <div>
            <dt>{t('uploader.hints')}</dt>
            <dd>{status?.hints?.length ? status.hints.join(', ') : fallbackDash}</dd>
          </div>
        </dl>
      </aside>
    </div>
  )
}

export default CadUploader
