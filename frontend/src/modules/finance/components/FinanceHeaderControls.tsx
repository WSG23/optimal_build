import { FormEvent, useEffect, useMemo, useState } from 'react'

import {
  Box,
  CircularProgress,
  Typography,
  alpha,
  useTheme,
} from '@mui/material'
import { KeyboardArrowDown, Refresh } from '@mui/icons-material'

import { Button } from '../../../components/canonical/Button'
import { useTranslation } from '../../../i18n'

export interface FinanceProjectOption {
  id: string
  label: string
  projectName?: string | null
  capturedAt?: string | null
}

interface FinanceHeaderControlsProps {
  selectedProjectId: string
  selectedProjectName?: string | null
  options: FinanceProjectOption[]
  onProjectChange: (projectId: string, projectName?: string | null) => void
  onRefresh: () => void
  refreshing: boolean
  onExportCsv: () => void
  exporting: boolean
  exportDisabled: boolean
}

export function FinanceHeaderControls({
  selectedProjectId,
  selectedProjectName,
  options,
  onProjectChange,
  onRefresh,
  refreshing,
  onExportCsv,
  exporting,
  exportDisabled,
}: FinanceHeaderControlsProps) {
  const { t } = useTranslation()
  const theme = useTheme()

  const [isManual, setIsManual] = useState(false)
  const [manualId, setManualId] = useState(selectedProjectId)

  useEffect(() => {
    setManualId(selectedProjectId)
  }, [selectedProjectId])

  const recentOptions = useMemo(() => {
    const seen = new Set<string>()
    return options.filter((option) => {
      if (seen.has(option.id)) return false
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

  const helperLabel =
    selectedProjectName ??
    t('finance.projectSelector.defaultLabel', { id: selectedProjectId })

  const selectOptions = useMemo(() => {
    if (!selectedProjectId) return recentOptions
    if (recentOptions.some((option) => option.id === selectedProjectId)) {
      return recentOptions
    }
    return [
      { id: selectedProjectId, label: helperLabel, projectName: helperLabel },
      ...recentOptions,
    ]
  }, [helperLabel, recentOptions, selectedProjectId])

  const selectValue = selectedOptionValue || selectedProjectId

  const handleManualSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const trimmed = manualId.trim()
    if (!trimmed) return
    onProjectChange(trimmed, null)
    setIsManual(false)
  }

  const handleOptionChange = (value: string) => {
    if (!value) return
    if (value === 'manual') {
      setIsManual(true)
      return
    }
    const option = recentOptions.find((item) => item.id === value)
    if (!option) return
    onProjectChange(option.id, option.projectName ?? option.label)
    setIsManual(false)
  }

  const divider = (
    <Box
      aria-hidden
      sx={{
        width: 1,
        height: '60%',
        bgcolor: alpha(theme.palette.divider, 0.6),
      }}
    />
  )

  if (isManual) {
    return (
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--ob-space-100)',
        }}
      >
        <Box
          component="form"
          onSubmit={handleManualSubmit}
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--ob-space-100)',
          }}
        >
          <Box
            component="input"
            value={manualId}
            onChange={(event) =>
              setManualId((event.target as HTMLInputElement).value)
            }
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
            onClick={() => setIsManual(false)}
          >
            {t('common.actions.cancel')}
          </Button>
        </Box>
      </Box>
    )
  }

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        height: 'var(--ob-space-250)',
        border: 'var(--ob-border-fine-strong)',
        borderRadius: 'var(--ob-radius-md)',
        bgcolor: alpha(theme.palette.background.paper, 0.75),
        backdropFilter: 'blur(var(--ob-blur-sm))',
        overflow: 'hidden',
        width: { xs: '100%', sm: 'auto' },
        maxWidth: { xs: '100%', sm: 'var(--ob-size-finance-header-controls)' },
        minWidth: 0,
        flexShrink: 1,
      }}
    >
      {/* Project selector segment */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--ob-space-100)',
          px: 'var(--ob-space-150)',
          minWidth: 0,
          flexShrink: 1,
        }}
      >
        <Typography
          sx={{
            fontSize: 'var(--ob-font-size-xs)',
            fontWeight: 800,
            letterSpacing: 'var(--ob-letter-spacing-wider)',
            color: 'text.secondary',
            textTransform: 'uppercase',
            whiteSpace: 'nowrap',
          }}
        >
          {t('finance.projectSelector.projectLabel', {
            defaultValue: 'Project',
          })}
        </Typography>

        <Box sx={{ position: 'relative', minWidth: 0 }}>
          <Box
            component="select"
            value={selectValue}
            onChange={(event) =>
              handleOptionChange((event.target as HTMLSelectElement).value)
            }
            aria-label={t('finance.projectSelector.title')}
            sx={{
              height: 'var(--ob-space-250)',
              // Keep compact and readable; don't allow this segment to expand
              // so wide that it pushes Export out of view.
              width: {
                xs: '100%',
                sm: 'var(--ob-size-finance-project-select)',
              },
              maxWidth: 'var(--ob-size-finance-project-select)',
              minWidth: 0,
              border: 0,
              outline: 'none',
              bgcolor: 'transparent',
              color: 'text.primary',
              fontSize: 'var(--ob-font-size-sm)',
              fontWeight: 700,
              fontFamily: 'var(--ob-font-family-base)',
              appearance: 'none',
              pr: 'var(--ob-space-250)',
              pl: 0,
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              cursor: 'pointer',
            }}
          >
            {selectOptions.map((option) => (
              <option key={option.id} value={option.id}>
                {option.label}
              </option>
            ))}
            <option value="manual">
              + {t('finance.projectSelector.enterManualId')}
            </option>
          </Box>
          <Box
            aria-hidden
            sx={{
              position: 'absolute',
              right: 'var(--ob-space-075)',
              top: '50%',
              transform: 'translateY(-50%)',
              color: 'text.secondary',
              pointerEvents: 'none',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <KeyboardArrowDown fontSize="small" />
          </Box>
        </Box>
      </Box>

      {divider}

      {/* Refresh */}
      <Button
        size="sm"
        variant="ghost"
        onClick={onRefresh}
        aria-label={t('finance.actions.refresh')}
        title={t('finance.actions.refresh')}
        disabled={refreshing}
        sx={{
          height: '100%',
          minWidth: 'var(--ob-space-250)',
          width: 'var(--ob-space-250)',
          px: 0,
          borderRadius: 0,
          flexShrink: 0,
        }}
      >
        {refreshing ? (
          <CircularProgress size={16} sx={{ color: 'inherit' }} />
        ) : (
          <Refresh fontSize="small" />
        )}
      </Button>

      {divider}

      {/* Export */}
      <Button
        size="sm"
        variant="ghost"
        onClick={onExportCsv}
        disabled={exportDisabled || exporting}
        aria-label={t('finance.actions.exportCsv')}
        title={t('finance.actions.exportCsv')}
        sx={{
          height: '100%',
          px: 'var(--ob-space-150)',
          borderRadius: 0,
          fontWeight: 800,
          letterSpacing: 'var(--ob-letter-spacing-wider)',
          textTransform: 'uppercase',
          whiteSpace: 'nowrap',
          minWidth: 'unset',
          width: 'var(--ob-size-finance-export-button)',
          flexShrink: 0,
          justifyContent: 'center',
        }}
      >
        {exporting ? (
          <CircularProgress size={16} sx={{ color: 'inherit' }} />
        ) : (
          t('finance.actions.exportCsv')
        )}
      </Button>
    </Box>
  )
}

export default FinanceHeaderControls
