import { useState } from 'react'

import { useLocale } from '../../i18n/LocaleContext'

interface ExportDialogProps {
  formats?: string[]
  onExport?: (format: string) => void
  disabled?: boolean
}

const DEFAULT_FORMATS = ['DXF', 'GeoJSON', 'CSV']

export function ExportDialog({ formats = DEFAULT_FORMATS, onExport, disabled = false }: ExportDialogProps) {
  const { strings } = useLocale()
  const [open, setOpen] = useState(false)

  const handleExport = (format: string) => {
    onExport?.(format)
    setOpen(false)
  }

  return (
    <section className="cad-panel">
      <h3>{strings.panels.exportTitle}</h3>
      <p>{strings.panels.exportSubtitle}</p>
      <button type="button" onClick={() => setOpen((value) => !value)} disabled={disabled}>
        {strings.detection.exportCta}
      </button>
      {open && (
        <ul className="cad-export">
          {formats.map((format) => (
            <li key={format}>
              <button type="button" onClick={() => handleExport(format)} disabled={disabled}>
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
