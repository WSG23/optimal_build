import { ExpandMore, FileDownload } from '@mui/icons-material'
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Button,
  TextField,
  InputAdornment,
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
  t?: (key: string, options?: Record<string, unknown>) => string
}

export function FinancialSettingsPanel({
  financialInputs,
  financialErrors,
  onFinancialChange,
  t: _t,
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
        onChange={() => setExpanded(!expanded)}
        sx={{
          boxShadow: 'none',
          background: 'transparent',
          '&:before': { display: 'none' },
          border: '1px solid var(--ob-color-border-premium)',
          borderRadius: 'var(--ob-radius-lg) !important',
          marginTop: 'var(--ob-space-4) !important',
          overflow: 'hidden',
          transition: 'border-color 0.2s',
          '&:hover': {
            borderColor: 'rgba(0,0,0,0.12)',
          },
        }}
      >
        <AccordionSummary
          expandIcon={
            <ExpandMore sx={{ color: 'rgba(255,255,255,0.5)' }} />
          }
          sx={{
            padding: 'var(--ob-space-4)',
            '& .MuiAccordionSummary-content': { margin: 0 },
          }}
        >
          <header>
            <h2
              style={{
                margin: 0,
                fontSize: '1rem',
                fontWeight: 600,
                color: 'rgba(255,255,255,0.9)',
                letterSpacing: '0.02em',
              }}
            >
              Financial Modeling
            </h2>
            <p
              style={{
                margin: '4px 0 0',
                fontSize: '0.75rem',
                color: 'rgba(255,255,255,0.5)',
                textTransform: 'uppercase',
                letterSpacing: '0.1em',
              }}
            >
              Investment Parameters
            </p>
          </header>
        </AccordionSummary>

        <AccordionDetails
          sx={{ padding: '0 var(--ob-space-4) var(--ob-space-6)' }}
        >
          <div className="feasibility-assumptions__grid">
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
              sx={{
                '& .MuiOutlinedInput-root': {
                  color: 'rgba(255,255,255,0.9)',
                  '& fieldset': { borderColor: 'rgba(255,255,255,0.2)' },
                  '&:hover fieldset': { borderColor: 'rgba(255,255,255,0.4)' },
                  '&.Mui-focused fieldset': { borderColor: '#06b6d4' },
                },
                '& .MuiInputLabel-root': { color: 'rgba(255,255,255,0.7)' },
                '& .MuiInputLabel-root.Mui-focused': { color: '#06b6d4' },
                '& .MuiInputAdornment-root': { color: 'rgba(255,255,255,0.5)' },
              }}
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
              sx={{
                mt: 2,
                '& .MuiOutlinedInput-root': {
                  color: 'rgba(255,255,255,0.9)',
                  '& fieldset': { borderColor: 'rgba(255,255,255,0.2)' },
                  '&:hover fieldset': { borderColor: 'rgba(255,255,255,0.4)' },
                  '&.Mui-focused fieldset': { borderColor: '#06b6d4' },
                },
                '& .MuiInputLabel-root': { color: 'rgba(255,255,255,0.7)' },
                '& .MuiInputLabel-root.Mui-focused': { color: '#06b6d4' },
                '& .MuiInputAdornment-root': { color: 'rgba(255,255,255,0.5)' },
              }}
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
              sx={{
                mt: 2,
                '& .MuiOutlinedInput-root': {
                  color: 'rgba(255,255,255,0.9)',
                  '& fieldset': { borderColor: 'rgba(255,255,255,0.2)' },
                  '&:hover fieldset': { borderColor: 'rgba(255,255,255,0.4)' },
                  '&.Mui-focused fieldset': { borderColor: '#06b6d4' },
                },
                '& .MuiInputLabel-root': { color: 'rgba(255,255,255,0.7)' },
                '& .MuiInputLabel-root.Mui-focused': { color: '#06b6d4' },
                '& .MuiInputAdornment-root': { color: 'rgba(255,255,255,0.5)' },
              }}
            />
          </div>

          <div
            style={{
              marginTop: '1.5rem',
              display: 'flex',
              justifyContent: 'flex-end',
            }}
          >
            <Button
              variant="outlined"
              startIcon={<FileDownload />}
              onClick={handleExportArgus}
              sx={{
                textTransform: 'none',
                color: 'var(--ob-color-text-body)',
                borderColor: 'var(--ob-color-border-premium)',
              }}
            >
              Export ARGUS
            </Button>
          </div>
        </AccordionDetails>
      </Accordion>
    </section>
  )
}
