import { useTranslation } from '../../../i18n'

interface FinanceScenarioDeleteDialogProps {
  open: boolean
  scenarioName: string
  pending?: boolean
  onConfirm: () => void
  onCancel: () => void
}

export function FinanceScenarioDeleteDialog({
  open,
  scenarioName,
  pending = false,
  onConfirm,
  onCancel,
}: FinanceScenarioDeleteDialogProps) {
  const { t } = useTranslation()

  if (!open) {
    return null
  }

  return (
    <div
      className="finance-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="finance-delete-dialog-title"
    >
      <div className="finance-modal__content">
        <h3 id="finance-delete-dialog-title">
          {t('finance.dialogs.deleteScenario.title')}
        </h3>
        <p>
          {t('finance.dialogs.deleteScenario.body', {
            name: scenarioName,
          })}
        </p>
        <div className="finance-modal__actions">
          <button
            type="button"
            className="finance-modal__button"
            onClick={onCancel}
            disabled={pending}
          >
            {t('finance.dialogs.deleteScenario.cancel')}
          </button>
          <button
            type="button"
            className="finance-modal__button finance-modal__danger"
            onClick={onConfirm}
            disabled={pending}
          >
            {pending
              ? t('finance.dialogs.deleteScenario.deleting')
              : t('finance.dialogs.deleteScenario.confirm')}
          </button>
        </div>
      </div>
    </div>
  )
}
