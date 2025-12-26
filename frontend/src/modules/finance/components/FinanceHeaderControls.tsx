import { FormEvent, useEffect, useMemo, useState } from 'react'

import {
  Box,
  CircularProgress,
  Menu,
  MenuItem,
  Typography,
  alpha,
  useMediaQuery,
  useTheme,
} from '@mui/material'
import {
  FileDownload as FileDownloadIcon,
  KeyboardArrowDown,
  Refresh,
} from '@mui/icons-material'

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
  const showExportLabel = useMediaQuery(theme.breakpoints.up('md'))

  const [isManual, setIsManual] = useState(false)
  const [manualId, setManualId] = useState(selectedProjectId)
  const [projectMenuAnchor, setProjectMenuAnchor] =
    useState<HTMLElement | null>(null)

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
  const selectedLabel =
    selectOptions.find((option) => option.id === selectValue)?.label ??
    helperLabel

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
      setProjectMenuAnchor(null)
      return
    }
    const option = recentOptions.find((item) => item.id === value)
    if (!option) return
    onProjectChange(option.id, option.projectName ?? option.label)
    setIsManual(false)
    setProjectMenuAnchor(null)
  }

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
        display: 'inline-flex',
        alignItems: 'stretch',
        height: 'var(--ob-space-250)',
        border: 'var(--ob-border-fine-strong)',
        borderRadius: 'var(--ob-radius-md)',
        bgcolor: alpha(theme.palette.background.paper, 0.75),
        backdropFilter: 'blur(var(--ob-blur-sm))',
        overflow: 'hidden',
        width: 'fit-content',
        maxWidth: '100%',
        minWidth: 0,
        flexShrink: 1,
      }}
    >
      {/* Label segment */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          px: 'var(--ob-space-150)',
          borderRight: 1,
          borderColor: alpha(theme.palette.divider, 0.6),
          minWidth: 0,
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
            flexShrink: 0,
          }}
        >
          {t('finance.projectSelector.projectLabel', {
            defaultValue: 'Project',
          })}
        </Typography>
      </Box>

      {/* Project selector segment */}
      <Box
        sx={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 'var(--ob-space-075)',
          px: 'var(--ob-space-150)',
          borderRight: 1,
          borderColor: alpha(theme.palette.divider, 0.6),
          minWidth: 0,
          flex: '0 1 auto',
          width: 'fit-content',
          maxWidth: 'var(--ob-size-finance-project-select)',
          cursor: 'pointer',
          userSelect: 'none',
        }}
        role="button"
        tabIndex={0}
        aria-label={t('finance.projectSelector.title')}
        onClick={(event) => setProjectMenuAnchor(event.currentTarget)}
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault()
            setProjectMenuAnchor(event.currentTarget as HTMLElement)
          }
        }}
      >
        <Typography
          sx={{
            color: 'text.primary',
            fontSize: 'var(--ob-font-size-sm)',
            fontWeight: 700,
            fontFamily: 'var(--ob-font-family-base)',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            minWidth: 0,
            maxWidth: '100%',
          }}
        >
          {selectedLabel}
        </Typography>
        <Box aria-hidden sx={{ color: 'text.secondary', display: 'flex' }}>
          <KeyboardArrowDown fontSize="small" />
        </Box>
      </Box>
      <Menu
        anchorEl={projectMenuAnchor}
        open={Boolean(projectMenuAnchor)}
        onClose={() => setProjectMenuAnchor(null)}
        slotProps={{
          paper: {
            sx: {
              mt: 'var(--ob-space-050)',
              borderRadius: 'var(--ob-radius-md)',
              border: 'var(--ob-border-fine-strong)',
              bgcolor: alpha(theme.palette.background.paper, 0.95),
              backdropFilter: 'blur(var(--ob-blur-sm))',
            },
          },
        }}
      >
        {selectOptions.map((option) => (
          <MenuItem
            key={option.id}
            selected={option.id === selectValue}
            onClick={() => handleOptionChange(option.id)}
            sx={{
              fontSize: 'var(--ob-font-size-sm)',
              fontWeight: option.id === selectValue ? 700 : 500,
              minWidth: 'var(--ob-size-finance-project-select)',
            }}
          >
            {option.label}
          </MenuItem>
        ))}
        <MenuItem
          onClick={() => handleOptionChange('manual')}
          sx={{
            fontSize: 'var(--ob-font-size-sm)',
            color: 'text.secondary',
            minWidth: 'var(--ob-size-finance-project-select)',
          }}
        >
          + {t('finance.projectSelector.enterManualId')}
        </MenuItem>
      </Menu>

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
          minWidth: 0,
          px: 0,
          borderRadius: 0,
          flexShrink: 0,
          borderRight: 1,
          borderColor: alpha(theme.palette.divider, 0.6),
        }}
      >
        {refreshing ? (
          <CircularProgress size={16} sx={{ color: 'inherit' }} />
        ) : (
          <Refresh fontSize="small" />
        )}
      </Button>

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
          minWidth: 0,
          flexShrink: 0,
          justifyContent: 'center',
        }}
      >
        {exporting ? (
          <CircularProgress size={16} sx={{ color: 'inherit' }} />
        ) : (
          <>
            <FileDownloadIcon fontSize="small" />
            {showExportLabel ? t('finance.actions.exportCsv') : null}
          </>
        )}
      </Button>
    </Box>
  )
}

export default FinanceHeaderControls
