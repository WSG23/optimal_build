import { ChangeEvent, DragEvent, useRef, useState } from 'react'

import type { CadImportSummary, ParseStatusUpdate } from '../../api/client'
import { useTranslation } from '../../i18n'

interface CadUploaderProps {
  onUpload: (file: File) => void
  isUploading?: boolean
  status?: ParseStatusUpdate | null
  summary?: CadImportSummary | null
}

export function CadUploader({ onUpload, isUploading = false, status, summary }: CadUploaderProps) {
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

  const latestStatus = (() => {
    switch (status?.status) {
      case 'completed':
        return t('uploader.ready')
      case 'failed':
        return t('uploader.error')
      case 'queued':
      case 'running':
      case 'pending':
        return t('uploader.parsing')
      default:
        return null
    }
  })()

  const fallbackDash = t('common.fallback.dash')
  const detectedFloors = status?.detectedFloors ?? summary?.detectedFloors ?? []
  const detectedUnits = status?.detectedUnits ?? summary?.detectedUnits ?? []

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
          accept=".dxf,.ifc,.json,.pdf,.svg,.jpg,.jpeg,.png"
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
        {summary && <p className="cad-uploader__filename">{summary.fileName}</p>}
        {latestStatus ? <p>{latestStatus}</p> : <p>{t('uploader.parsing')}</p>}
        {status?.error && <p className="cad-uploader__message">{status.error}</p>}
        <dl className="cad-uploader__meta">
          <div>
            <dt>{t('uploader.floors')}</dt>
            <dd>
              {detectedFloors.length
                ? detectedFloors.map((floor) => floor.name).join(', ')
                : fallbackDash}
            </dd>
          </div>
          <div>
            <dt>{t('uploader.units')}</dt>
            <dd>{detectedUnits.length > 0 ? detectedUnits.length : fallbackDash}</dd>
          </div>
        </dl>
      </aside>
    </div>
  )
}

export default CadUploader
