import { useLocale } from '../../i18n/LocaleContext'

interface BulkReviewControlsProps {
  pendingCount: number
  onApproveAll: () => void
  onRejectAll: () => void
  disabled?: boolean
}

export function BulkReviewControls({
  pendingCount,
  onApproveAll,
  onRejectAll,
  disabled = false,
}: BulkReviewControlsProps) {
  const { strings } = useLocale()

  return (
    <section className="cad-panel">
      <h3>{strings.controls.pending}</h3>
      <p>{pendingCount} {strings.controls.pending.toLowerCase()}</p>
      <div className="cad-bulk-controls">
        <button type="button" onClick={onApproveAll} disabled={disabled || pendingCount === 0}>
          {strings.controls.approveAll}
        </button>
        <button type="button" onClick={onRejectAll} disabled={disabled || pendingCount === 0}>
          {strings.controls.rejectAll}
        </button>
      </div>
      {disabled && <p className="cad-panel__hint">{strings.controls.locked}</p>}
    </section>
  )
}

export default BulkReviewControls
