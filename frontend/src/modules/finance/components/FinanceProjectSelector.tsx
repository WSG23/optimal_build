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
  const [isExpanded, setIsExpanded] = useState(false)
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
    const match = recentOptions.find(
      (option) => option.id === selectedProjectId,
    )
    return match ? match.id : ''
  }, [recentOptions, selectedProjectId])

  const handleManualSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const trimmed = manualId.trim()
    if (!trimmed) {
      return
    }
    onProjectChange(trimmed, null)
    setIsExpanded(false)
  }

  const handleOptionChange = (value: string) => {
    if (!value) {
      return
    }
    if (value === 'manual') {
      setIsExpanded(true)
      return
    }
    const option = recentOptions.find((item) => item.id === value)
    if (!option) {
      return
    }
    onProjectChange(option.id, option.projectName ?? option.label)
    setIsExpanded(false)
  }

  const helperLabel =
    selectedProjectName ??
    t('finance.projectSelector.defaultLabel', {
      id: selectedProjectId,
    })

  return (
    <section className="finance-project-selector" aria-live="polite">
      <div className="finance-project-selector__header">
        <div>
          <h2>{t('finance.projectSelector.title')}</h2>
        </div>
        <div className="finance-project-selector__controls">
          <span className="finance-project-selector__current">
            {t('finance.projectSelector.current', { value: helperLabel })}
          </span>
          {!isExpanded ? (
            <select
              className="finance-project-selector__select"
              value={selectedOptionValue}
              onChange={(event) => handleOptionChange(event.target.value)}
            >
              <option value="" disabled>
                {t('finance.projectSelector.pickPlaceholder')}
              </option>
              {recentOptions.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.label}
                </option>
              ))}
              <option value="manual">
                + {t('finance.projectSelector.enterManualId')}
              </option>
            </select>
          ) : null}
          {onRefresh && (
            <button
              type="button"
              className="finance-project-selector__refresh-icon"
              onClick={onRefresh}
              title={t('finance.projectSelector.refresh')}
            >
              ↻
            </button>
          )}
        </div>
      </div>

      {isExpanded ? (
        <div className="finance-project-selector__body">
          <form
            className="finance-project-selector__form"
            onSubmit={handleManualSubmit}
          >
            <label htmlFor="finance-project-id" className="sr-only">
              {t('finance.projectSelector.inputLabel')}
            </label>
            <div className="finance-project-selector__input-row">
              <input
                id="finance-project-id"
                value={manualId}
                onChange={(event) => setManualId(event.target.value)}
                placeholder={t('finance.projectSelector.inputPlaceholder')}
                autoFocus
              />
              <button type="submit">
                {t('finance.projectSelector.submit')}
              </button>
              <button type="button" onClick={() => setIsExpanded(false)}>
                {t('common.actions.cancel')}
              </button>
            </div>
          </form>
        </div>
      ) : null}
    </section>
  )
}
