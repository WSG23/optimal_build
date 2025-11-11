import { FormEvent, useEffect, useMemo, useState } from 'react'

import { useTranslation } from '../../../i18n'

export interface FinanceProjectOption {
  id: string
  label: string
  projectName?: string | null
  capturedAt?: string | null
}

interface FinanceProjectSelectorProps {
  selectedProjectId: string
  selectedProjectName?: string | null
  options: FinanceProjectOption[]
  onProjectChange: (projectId: string, projectName?: string | null) => void
  onRefresh?: () => void
}

export function FinanceProjectSelector({
  selectedProjectId,
  selectedProjectName,
  options,
  onProjectChange,
  onRefresh,
}: FinanceProjectSelectorProps) {
  const { t } = useTranslation()
  const [manualId, setManualId] = useState(selectedProjectId)

  useEffect(() => {
    setManualId(selectedProjectId)
  }, [selectedProjectId])

  const recentOptions = useMemo(() => {
    const seen = new Set<string>()
    return options.filter((option) => {
      if (seen.has(option.id)) {
        return false
      }
      seen.add(option.id)
      return true
    })
  }, [options])

  const selectedOptionValue = useMemo(() => {
    const match = recentOptions.find((option) => option.id === selectedProjectId)
    return match ? match.id : ''
  }, [recentOptions, selectedProjectId])

  const handleManualSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const trimmed = manualId.trim()
    if (!trimmed) {
      return
    }
    onProjectChange(trimmed, null)
  }

  const handleOptionChange = (value: string) => {
    if (!value) {
      return
    }
    const option = recentOptions.find((item) => item.id === value)
    if (!option) {
      return
    }
    onProjectChange(option.id, option.projectName ?? option.label)
  }

  const helperLabel =
    selectedProjectName ??
    t('finance.projectSelector.defaultLabel', {
      id: selectedProjectId,
    })

  return (
    <section className="finance-project-selector" aria-live="polite">
      <header className="finance-project-selector__header">
        <div>
          <h2>{t('finance.projectSelector.title')}</h2>
          <p>{t('finance.projectSelector.description')}</p>
        </div>
        <p className="finance-project-selector__active">
          {t('finance.projectSelector.current', { value: helperLabel })}
        </p>
      </header>
      <div className="finance-project-selector__body">
        <form
          className="finance-project-selector__form"
          onSubmit={handleManualSubmit}
        >
          <label htmlFor="finance-project-id">
            {t('finance.projectSelector.inputLabel')}
          </label>
          <div className="finance-project-selector__input-row">
            <input
              id="finance-project-id"
              value={manualId}
              onChange={(event) => setManualId(event.target.value)}
              placeholder={t('finance.projectSelector.inputPlaceholder')}
            />
            <button type="submit">
              {t('finance.projectSelector.submit')}
            </button>
          </div>
        </form>
        <div className="finance-project-selector__recent">
          <div className="finance-project-selector__recent-header">
            <label htmlFor="finance-recent-projects">
              {t('finance.projectSelector.recentLabel')}
            </label>
            <button
              type="button"
              className="finance-project-selector__refresh"
              onClick={onRefresh}
            >
              {t('finance.projectSelector.refresh')}
            </button>
          </div>
          {recentOptions.length > 0 ? (
            <select
              id="finance-recent-projects"
              value={selectedOptionValue}
              onChange={(event) => handleOptionChange(event.target.value)}
            >
              <option value="">
                {t('finance.projectSelector.pickPlaceholder')}
              </option>
              {recentOptions.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.label}
                </option>
              ))}
            </select>
          ) : (
            <p className="finance-project-selector__empty">
              {t('finance.projectSelector.empty')}
            </p>
          )}
          <p className="finance-project-selector__hint">
            {t('finance.projectSelector.hint')}
          </p>
        </div>
      </div>
    </section>
  )
}
