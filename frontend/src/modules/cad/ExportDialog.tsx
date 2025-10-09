import { useState } from 'react'

import { useTranslation } from '../../i18n'

interface ExportDialogProps {
  formats?: string[]
  onExport?: (format: string) => void
  disabled?: boolean
  defaultOpen?: boolean
  pendingCount?: number
}

const DEFAULT_FORMATS = ['DXF', 'DWG', 'IFC', 'PDF']

export function ExportDialog({
  formats = DEFAULT_FORMATS,
  onExport,
  disabled = false,
  defaultOpen = false,
  pendingCount = 0,
}: ExportDialogProps) {
  const { t } = useTranslation()
  const [open, setOpen] = useState(defaultOpen)

  const handleExport = (format: string) => {
    onExport?.(format)
    setOpen(false)
  }

  return (
    <section className="cad-panel">
      <h3>{t('panels.exportTitle')}</h3>
      <p>{t('panels.exportSubtitle')}</p>
      {pendingCount > 0 && (
        <p className="cad-export__pending">
          <span className="cad-export__pending-text">
            {pendingCount === 1
              ? t('detection.pendingNoticeSingle')
              : t('detection.pendingNotice', { count: pendingCount })}
          </span>
          <button
            type="button"
            className="cad-export__pending-info"
            title={t('detection.pendingTooltip')}
            aria-label={t('detection.pendingTooltip')}
          >
            i
          </button>
        </p>
      )}
      <button
        type="button"
        onClick={() => {
          setOpen((value) => !value)
        }}
        disabled={disabled}
      >
        {t('detection.exportCta')}
      </button>
      {open && (
        <ul className="cad-export">
          {formats.map((format) => (
            <li key={format}>
              <button
                type="button"
                onClick={() => {
                  handleExport(format)
                }}
                disabled={disabled}
              >
                {format}
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

export default ExportDialog
