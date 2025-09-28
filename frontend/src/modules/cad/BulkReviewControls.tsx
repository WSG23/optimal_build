import { useTranslation } from '../../i18n'

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
  const { t } = useTranslation()

  return (
    <section className="cad-panel">
      <h3>{t('controls.pending')}</h3>
      <p>
        {pendingCount} {t('controls.pending')}
      </p>
      <div className="cad-bulk-controls">
        <button
          type="button"
          onClick={onApproveAll}
          disabled={disabled || pendingCount === 0}
        >
          {t('controls.approveAll')}
        </button>
        <button
          type="button"
          onClick={onRejectAll}
          disabled={disabled || pendingCount === 0}
        >
          {t('controls.rejectAll')}
        </button>
      </div>
      {disabled && <p className="cad-panel__hint">{t('controls.locked')}</p>}
    </section>
  )
}

export default BulkReviewControls
