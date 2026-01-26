import { ExpandMore, FileDownload, CloudUpload } from '@mui/icons-material'
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Button,
  TextField,
  InputAdornment,
  FormControlLabel,
  Switch,
  Box,
} from '@mui/material'
import type { ChangeEvent } from 'react'
import { useState } from 'react'

import type { FinancialAssumptions } from '../types'

interface FinancialSettingsPanelProps {
  financialInputs: FinancialAssumptions
  financialErrors: Partial<Record<keyof FinancialAssumptions, string>>
  onFinancialChange: (
    key: keyof FinancialAssumptions,
  ) => (event: ChangeEvent<HTMLInputElement>) => void
  onVdrUploadToggle?: (enabled: boolean) => void
  vdrUploadEnabled?: boolean
}

// Common TextField styling for theme-aware colors
const textFieldSx = {
  '& .MuiOutlinedInput-root': {
    color: 'var(--ob-color-text-primary)',
    '& fieldset': { borderColor: 'var(--ob-color-border-subtle)' },
    '&:hover fieldset': { borderColor: 'var(--ob-color-border-neutral)' },
    '&.Mui-focused fieldset': { borderColor: 'var(--ob-color-brand-primary)' },
  },
  '& .MuiInputLabel-root': { color: 'var(--ob-color-text-secondary)' },
  '& .MuiInputLabel-root.Mui-focused': {
    color: 'var(--ob-color-brand-primary)',
  },
  '& .MuiInputAdornment-root': { color: 'var(--ob-color-text-muted)' },
}

export function FinancialSettingsPanel({
  financialInputs,
  financialErrors,
  onFinancialChange,
  onVdrUploadToggle,
  vdrUploadEnabled = false,
}: FinancialSettingsPanelProps) {
  const [expanded, setExpanded] = useState(false)

  const handleExportArgus = () => {
    // Stub for ARGUS export
    console.log('Exporting ARGUS XML...', financialInputs)
    const blob = new Blob(
      ['<ArgusExchange><Stub>Active</Stub></ArgusExchange>'],
      {
        type: 'application/xml',
      },
    )
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'project_argus.xml'
    a.click()
  }

  return (
    <section className="feasibility-financials">
      <Accordion
        expanded={expanded}
        onChange={() => {
          setExpanded(!expanded)
        }}
        sx={{
          boxShadow: 'none',
          background: 'var(--ob-color-bg-surface)',
          '&:before': { display: 'none' },
          border: '1px solid var(--ob-color-border-subtle)',
          borderRadius: 'var(--ob-radius-sm) !important',
          marginTop: '0 !important',
          overflow: 'hidden',
          transition: 'border-color 0.2s',
          '&:hover': {
            borderColor: 'var(--ob-color-border-neutral)',
          },
        }}
      >
        <AccordionSummary
          expandIcon={
            <ExpandMore sx={{ color: 'var(--ob-color-text-muted)' }} />
          }
          sx={{
            padding: 'var(--ob-space-075)',
            '& .MuiAccordionSummary-content': { margin: 0 },
          }}
        >
          <header>
            <h2
              style={{
                margin: 0,
                fontSize: 'var(--ob-font-size-base)',
                fontWeight: 600,
                color: 'var(--ob-color-text-primary)',
                letterSpacing: '0.02em',
              }}
            >
              Financial Modeling
            </h2>
            <p
              style={{
                margin: 'var(--ob-space-025) 0 0',
                fontSize: 'var(--ob-font-size-xs)',
                color: 'var(--ob-color-text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.1em',
              }}
            >
              Investment Parameters
            </p>
          </header>
        </AccordionSummary>

        <AccordionDetails
          sx={{ padding: '0 var(--ob-space-075) var(--ob-space-100)' }}
        >
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: 'var(--ob-space-075)',
            }}
          >
            <TextField
              label="Cap Rate (%)"
              value={financialInputs.capRatePercent}
              onChange={onFinancialChange('capRatePercent')}
              error={!!financialErrors.capRatePercent}
              helperText={financialErrors.capRatePercent}
              InputProps={{
                endAdornment: <InputAdornment position="end">%</InputAdornment>,
              }}
              variant="outlined"
              size="small"
              fullWidth
              sx={textFieldSx}
            />

            <TextField
              label="Interest Rate (%)"
              value={financialInputs.interestRatePercent}
              onChange={onFinancialChange('interestRatePercent')}
              error={!!financialErrors.interestRatePercent}
              helperText={financialErrors.interestRatePercent}
              InputProps={{
                endAdornment: <InputAdornment position="end">%</InputAdornment>,
              }}
              variant="outlined"
              size="small"
              fullWidth
              sx={textFieldSx}
            />

            <TextField
              label="Target Margin (CoC %)"
              value={financialInputs.targetMarginPercent}
              onChange={onFinancialChange('targetMarginPercent')}
              error={!!financialErrors.targetMarginPercent}
              helperText={financialErrors.targetMarginPercent}
              InputProps={{
                endAdornment: <InputAdornment position="end">%</InputAdornment>,
              }}
              variant="outlined"
              size="small"
              fullWidth
              sx={textFieldSx}
            />
          </Box>

          <Box
            sx={{
              marginTop: 'var(--ob-space-100)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            {/* VDR Upload Toggle */}
            <FormControlLabel
              control={
                <Switch
                  checked={vdrUploadEnabled}
                  onChange={(e) => onVdrUploadToggle?.(e.target.checked)}
                  sx={{
                    '& .MuiSwitch-switchBase.Mui-checked': {
                      color: 'var(--ob-color-brand-primary)',
                    },
                    '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                      backgroundColor: 'var(--ob-color-brand-primary)',
                    },
                  }}
                />
              }
              label={
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--ob-space-100)',
                  }}
                >
                  <CloudUpload
                    sx={{
                      fontSize: '1rem',
                      color: 'var(--ob-color-text-muted)',
                    }}
                  />
                  <span
                    style={{
                      fontSize: 'var(--ob-font-size-sm)',
                      color: 'var(--ob-color-text-secondary)',
                    }}
                  >
                    VDR Upload
                  </span>
                </Box>
              }
            />

            <Button
              variant="outlined"
              startIcon={<FileDownload />}
              onClick={handleExportArgus}
              sx={{
                textTransform: 'none',
                color: 'var(--ob-color-text-primary)',
                borderColor: 'var(--ob-color-border-subtle)',
                '&:hover': {
                  borderColor: 'var(--ob-color-brand-primary)',
                  backgroundColor: 'var(--ob-color-action-hover)',
                },
              }}
            >
              Export ARGUS
            </Button>
          </Box>
        </AccordionDetails>
      </Accordion>
    </section>
  )
}
