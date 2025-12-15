import { FormEvent, useEffect, useMemo, useState } from 'react'

import { Box, Typography } from '@mui/material'
import { Refresh } from '@mui/icons-material'

import { Button } from '../../../components/canonical/Button'
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
  className?: string
}

export function FinanceProjectSelector({
  selectedProjectId,
  selectedProjectName,
  options,
  onProjectChange,
  onRefresh,
  className,
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

  if (isExpanded) {
    return (
      <Box className={className} sx={{ display: 'flex', alignItems: 'center' }}>
        <form
          onSubmit={handleManualSubmit}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--ob-space-100)',
          }}
        >
          <input
            value={manualId}
            onChange={(event) => setManualId(event.target.value)}
            placeholder={t('finance.projectSelector.inputPlaceholder')}
            autoFocus
            className="finance-project-selector__manual-input"
          />
          <Button type="submit" size="sm" variant="primary">
            {t('finance.projectSelector.submit')}
          </Button>
          <Button
            type="button"
            size="sm"
            variant="ghost"
            onClick={() => setIsExpanded(false)}
          >
            {t('common.actions.cancel')}
          </Button>
        </form>
      </Box>
    )
  }

  return (
    <Box
      className={className}
      sx={{ display: 'flex', alignItems: 'center', gap: 'var(--ob-space-150)' }}
    >
      {/* Framed Label */}
      <div className="finance-project-selector__label-frame">
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ whiteSpace: 'nowrap', fontWeight: 500 }}
        >
          {t('finance.projectSelector.current', { value: helperLabel })}
        </Typography>
      </div>

      {/* Framed Dropdown */}
      <div className="finance-project-selector__dropdown-wrapper">
        <select
          className="finance-project-selector__dropdown"
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
        <span className="finance-project-selector__dropdown-arrow">▼</span>
      </div>

      {onRefresh && (
        <Button
          variant="secondary"
          size="md"
          onClick={onRefresh}
          className="finance-project-selector__refresh-btn"
          title={t('finance.projectSelector.refresh')}
        >
          <Refresh fontSize="small" />
        </Button>
      )}
    </Box>
  )
}
