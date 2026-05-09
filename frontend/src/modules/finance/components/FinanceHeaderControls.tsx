import { FormEvent, useEffect, useMemo, useState } from 'react'

import {
  Box,
  CircularProgress,
  Menu,
  MenuItem,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material'
import FileDownloadIcon from '@mui/icons-material/FileDownload'
import UploadFileIcon from '@mui/icons-material/UploadFile'
import KeyboardArrowDown from '@mui/icons-material/KeyboardArrowDown'
import Refresh from '@mui/icons-material/Refresh'

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
  onImportWorkbook: () => void
  importingWorkbook: boolean
  importDisabled: boolean
  onExportWorkbook: () => void
  exportingWorkbook: boolean
  onExportCsv: () => void
  exportingCsv: boolean
  exportDisabled: boolean
}

export function FinanceHeaderControls({
  selectedProjectId,
  selectedProjectName,
  options,
  onProjectChange,
  onRefresh,
  refreshing,
  onImportWorkbook,
  importingWorkbook,
  importDisabled,
  onExportWorkbook,
  exportingWorkbook,
  onExportCsv,
  exportingCsv,
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
    selectedProjectName ||
    (selectedProjectId
      ? t('finance.projectSelector.defaultLabel', { id: selectedProjectId })
      : 'Select project')

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
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--ob-space-075)',
        flexWrap: 'nowrap',
        minWidth: 0,
        flexShrink: 1,
      }}
    >
      {/* Project selector */}
      <Button
        size="sm"
        variant="secondary"
        onClick={(event) => setProjectMenuAnchor(event.currentTarget)}
        aria-label={t('finance.projectSelector.title')}
        sx={{
          maxWidth: 'var(--ob-size-finance-project-select)',
          minWidth: 0,
        }}
      >
        <Typography
          sx={{
            fontSize: 'var(--ob-font-size-xs)',
            fontWeight: 'var(--ob-font-weight-semibold)',
            letterSpacing: '0.1em',
            color: 'text.secondary',
            whiteSpace: 'nowrap',
            mr: 'var(--ob-space-050)',
            flexShrink: 0,
          }}
        >
          {t('finance.projectSelector.projectLabel', {
            defaultValue: 'Project',
          })}
        </Typography>
        <Typography
          sx={{
            fontSize: 'var(--ob-font-size-sm)',
            fontWeight: 'var(--ob-font-weight-semibold)',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            minWidth: 0,
            color: 'text.primary',
          }}
        >
          {selectedLabel}
        </Typography>
        <KeyboardArrowDown
          fontSize="small"
          sx={{ color: 'text.secondary', ml: 'var(--ob-space-025)' }}
        />
      </Button>
      <Menu
        anchorEl={projectMenuAnchor}
        open={Boolean(projectMenuAnchor)}
        onClose={() => setProjectMenuAnchor(null)}
        slotProps={{
          paper: {
            sx: {
              mt: 'var(--ob-space-050)',
              borderRadius: 'var(--ob-radius-sm)',
              border: 'var(--ob-border-fine-strong)',
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
        sx={{ minWidth: 0, px: 'var(--ob-space-075)' }}
      >
        {refreshing ? (
          <CircularProgress size={16} sx={{ color: 'inherit' }} />
        ) : (
          <Refresh fontSize="small" />
        )}
      </Button>

      {/* Import */}
      <Button
        size="sm"
        variant="secondary"
        onClick={onImportWorkbook}
        disabled={importDisabled || importingWorkbook}
        aria-label={t('finance.actions.importWorkbook', {
          defaultValue: 'Import workbook',
        })}
        title={t('finance.actions.importWorkbook', {
          defaultValue: 'Import workbook',
        })}
      >
        {importingWorkbook ? (
          <CircularProgress size={16} sx={{ color: 'inherit' }} />
        ) : (
          <>
            <UploadFileIcon fontSize="small" />
            {showExportLabel
              ? t('finance.actions.importWorkbook', {
                  defaultValue: 'Import workbook',
                })
              : null}
          </>
        )}
      </Button>

      {/* Export workbook */}
      <Button
        size="sm"
        variant="secondary"
        onClick={onExportWorkbook}
        disabled={exportDisabled || exportingWorkbook}
        aria-label={t('finance.actions.exportWorkbook', {
          defaultValue: 'Export workbook',
        })}
        title={t('finance.actions.exportWorkbook', {
          defaultValue: 'Export workbook',
        })}
      >
        {exportingWorkbook ? (
          <CircularProgress size={16} sx={{ color: 'inherit' }} />
        ) : (
          <>
            <FileDownloadIcon fontSize="small" />
            {showExportLabel
              ? t('finance.actions.exportWorkbook', {
                  defaultValue: 'Export workbook',
                })
              : null}
          </>
        )}
      </Button>

      {/* Export CSV */}
      <Button
        size="sm"
        variant="ghost"
        onClick={onExportCsv}
        disabled={exportDisabled || exportingCsv}
        aria-label={t('finance.actions.exportCsv')}
        title={t('finance.actions.exportCsv')}
      >
        {exportingCsv ? (
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
