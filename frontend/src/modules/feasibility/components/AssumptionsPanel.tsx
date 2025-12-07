import { ExpandMore } from '@mui/icons-material'
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Slider,
} from '@mui/material'
import type { ChangeEvent } from 'react'
import { useState } from 'react'

import type { AssumptionInputs, AssumptionErrors } from '../types'
import { DEFAULT_ASSUMPTIONS } from '../types'

interface AssumptionsPanelProps {
  assumptionInputs: AssumptionInputs
  assumptionErrors: AssumptionErrors
  decimalFormatter: Intl.NumberFormat
  onAssumptionChange: (
    key: keyof AssumptionInputs,
  ) => (event: ChangeEvent<HTMLInputElement>) => void
  onResetAssumptions: () => void
  t: (key: string, options?: Record<string, unknown>) => string
}

export function AssumptionsPanel({
  assumptionInputs,
  assumptionErrors,
  decimalFormatter,
  onAssumptionChange,
  onResetAssumptions,
  t,
}: AssumptionsPanelProps) {
  // We keep the accordion open by default or let user toggle
  const [expanded, setExpanded] = useState(true)

  // Adapter for Slider (number) -> ChangeEvent (string)
  const handleSliderChange =
    (key: keyof AssumptionInputs) => (_: Event, value: number | number[]) => {
      const val = Array.isArray(value) ? value[0] : value
      // Create synthetic event to match existing hook signature
      const syntheticEvent = {
        target: { value: val.toString() },
      } as ChangeEvent<HTMLInputElement>
      onAssumptionChange(key)(syntheticEvent)
    }

  const renderAssumptionError = (key: keyof AssumptionInputs) => {
    const error = assumptionErrors[key]
    if (!error) {
      return null
    }
    const messageKey =
      error === 'required'
        ? 'wizard.assumptions.errors.required'
        : error === 'range'
          ? 'wizard.assumptions.errors.range'
          : 'wizard.assumptions.errors.invalid'
    return <p className="feasibility-assumptions__error">{t(messageKey)}</p>
  }

  return (
    <section className="feasibility-assumptions">
      <Accordion
        expanded={expanded}
        onChange={() => setExpanded(!expanded)}
        sx={{
          boxShadow: 'none',
          background: '#1A1A1A', // Darker card background as requested
          '&:before': { display: 'none' },
          border: '1px solid var(--ob-color-border-premium)',
          borderRadius: 'var(--ob-radius-lg) !important',
          marginTop: '0 !important',
          overflow: 'hidden',
          transition: 'border-color 0.2s',
          '&:hover': {
             borderColor: 'rgba(0,0,0,0.12)'
          }
        }}
      >
        <AccordionSummary
          expandIcon={<ExpandMore sx={{ color: 'var(--ob-color-text-muted)' }} />}
          sx={{
            padding: 'var(--ob-space-4)',
            '& .MuiAccordionSummary-content': { margin: 0 },
          }}
        >
          <header>
            <h2 className="text-heading" style={{ margin: 0 }}>
              {t('wizard.assumptions.title') || 'Design Parameters'}
            </h2>
            <p style={{ margin: '4px 0 0', fontSize: '0.875rem', color: 'var(--ob-color-text-muted)' }}>
              {t('wizard.assumptions.subtitle')}
            </p>
          </header>
        </AccordionSummary>

        <AccordionDetails sx={{ padding: '0 var(--ob-space-4) var(--ob-space-6)' }}>
          <div className="feasibility-assumptions__grid">
            {/* Floor to Floor */}
            <div className="feasibility-control-group" style={{ marginBottom: 'var(--ob-space-6)' }}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: 'var(--ob-space-3)',
                }}
              >
                <label htmlFor="assumption-floor" style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--ob-color-text-body)' }}>
                  {t('wizard.assumptions.fields.typFloorToFloor.label')}
                </label>
                <span style={{
                    fontSize: '0.8125rem',
                    fontWeight: 700,
                    color: 'var(--ob-color-accent)',
                    background: 'var(--ob-color-accent-light)',
                    padding: '2px 8px',
                    borderRadius: '4px'
                }}>
                  {assumptionInputs.typFloorToFloorM} m
                </span>
              </div>
              <Slider
                value={Number(assumptionInputs.typFloorToFloorM) || 3.0}
                onChange={handleSliderChange('typFloorToFloorM')}
                min={2.5}
                max={6.0}
                step={0.1}
                sx={{
                    color: 'var(--ob-color-accent)',
                    height: 6,
                    '& .MuiSlider-track': { border: 'none' },
                    '& .MuiSlider-thumb': {
                        height: 20,
                        width: 20,
                        backgroundColor: '#fff',
                        border: '2px solid currentColor',
                        '&:focus, &:hover, &.Mui-active, &.Mui-focusVisible': {
                            boxShadow: 'inherit',
                        },
                        '&:before': { display: 'none' },
                    },
                }}
              />
              <p className="feasibility-assumptions__hint" style={{ fontSize: '0.75rem', color: 'var(--ob-color-text-muted)', marginTop: '4px' }}>
                {t('wizard.assumptions.fields.typFloorToFloor.hint', {
                  value: decimalFormatter.format(DEFAULT_ASSUMPTIONS.typFloorToFloorM),
                })}
              </p>
              {renderAssumptionError('typFloorToFloorM')}
            </div>

            {/* Efficiency */}
            <div className="feasibility-control-group">
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: 'var(--ob-space-3)',
                }}
              >
                <label
                  htmlFor="assumption-efficiency"
                  style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--ob-color-text-body)' }}
                >
                  {t('wizard.assumptions.fields.efficiency.label')}
                </label>
                <span style={{
                    fontSize: '0.8125rem',
                    fontWeight: 700,
                    color: 'var(--ob-color-accent)',
                    background: 'var(--ob-color-accent-light)',
                    padding: '2px 8px',
                    borderRadius: '4px'
                }}>
                  {Math.round((Number(assumptionInputs.efficiencyRatio) || 0) * 100)}%
                </span>
              </div>

              <Slider
                value={Number(assumptionInputs.efficiencyRatio) || 0.8}
                onChange={handleSliderChange('efficiencyRatio')}
                min={0.5}
                max={0.95}
                step={0.01}
                sx={{
                    color: 'var(--ob-color-accent)',
                    height: 6,
                    '& .MuiSlider-track': { border: 'none' },
                    '& .MuiSlider-thumb': {
                        height: 20,
                        width: 20,
                        backgroundColor: '#fff',
                        border: '2px solid currentColor',
                        '&:focus, &:hover, &.Mui-active, &.Mui-focusVisible': {
                            boxShadow: 'inherit',
                        },
                        '&:before': { display: 'none' },
                    },
                }}
              />

              <p className="feasibility-assumptions__hint" style={{ fontSize: '0.75rem', color: 'var(--ob-color-text-muted)', marginTop: '4px' }}>
                {t('wizard.assumptions.fields.efficiency.hint', {
                  value: decimalFormatter.format(DEFAULT_ASSUMPTIONS.efficiencyRatio),
                })}
              </p>
              {renderAssumptionError('efficiencyRatio')}
            </div>

            {/* Engineering Divider */}
            <div style={{
                height: '1px',
                background: 'var(--ob-color-border-premium)',
                margin: 'var(--ob-space-6) 0'
            }} />

            <h3 className="text-eyebrow" style={{ marginBottom: 'var(--ob-space-4)' }}>
                {t('wizard.assumptions.engineering.title') || 'Engineering Constraints'}
            </h3>

            {/* Structure Type */}
            <div className="feasibility-control-group" style={{ marginBottom: 'var(--ob-space-6)' }}>
                <label className="text-body" style={{ fontWeight: 600, fontSize: '0.875rem', display: 'block', marginBottom: 'var(--ob-space-3)' }}>
                    {t('wizard.assumptions.fields.structure.label') || 'Structural Material'}
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
                    {[
                      { value: 'rc', label: 'Reinforced Concrete', icon: '🏢' }, // Fallback to emoji if icons fail, or use MUI Foundation
                      { value: 'steel', label: 'Steel Frame', icon: '🏗️' },
                      { value: 'mass_timber', label: 'Mass Timber', icon: '🌲' }
                    ].map((option) => (
                        <button
                            key={option.value}
                            type="button"
                            onClick={() => {
                                const syntheticEvent = { target: { value: option.value } } as ChangeEvent<HTMLInputElement>
                                onAssumptionChange('structureType')(syntheticEvent)
                            }}
                            className={`feasibility-card-select ${assumptionInputs.structureType === option.value ? 'selected' : ''}`}
                            style={{
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                justifyContent: 'center',
                                padding: '12px 8px',
                                gap: '8px',
                                fontSize: '0.75rem',
                                fontWeight: 600,
                                border: `1px solid ${assumptionInputs.structureType === option.value ? 'var(--ob-color-accent)' : 'var(--ob-color-border-premium)'}`,
                                background: assumptionInputs.structureType === option.value ? 'rgba(0, 123, 255, 0.05)' : 'white', // TODO: Use token
                                color: assumptionInputs.structureType === option.value ? 'var(--ob-color-accent)' : 'var(--ob-color-text-muted)',
                                borderRadius: 'var(--ob-radius-lg)',
                                cursor: 'pointer',
                                transition: 'all 0.2s',
                                boxShadow: assumptionInputs.structureType === option.value ? '0 0 0 1px var(--ob-color-accent)' : 'none'
                             }}
                            title={option.label}
                        >
                            <span style={{ fontSize: '1.5rem', lineHeight: 1 }}>{option.icon}</span>
                            <span style={{ textAlign: 'center', lineHeight: 1.2 }}>{option.label}</span>
                        </button>
                    ))}
                </div>
            </div>

            {/* MEP Load */}
            <div className="feasibility-control-group">
                <div
                style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: 'var(--ob-space-2)',
                }}
                >
                <label style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--ob-color-text-body)' }}>
                    {t('wizard.assumptions.fields.mep.label') || 'MEP Load'}
                </label>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                   <Slider
                    value={Number(assumptionInputs.mepLoadWpsm) || 150}
                    onChange={handleSliderChange('mepLoadWpsm')}
                    min={50}
                    max={500}
                    step={10}
                    sx={{
                        flex: 1,
                        color: 'var(--ob-color-accent)',
                        height: 6,
                        '& .MuiSlider-track': { border: 'none' },
                        '& .MuiSlider-thumb': {
                            height: 20,
                            width: 20,
                            backgroundColor: '#fff',
                            border: '2px solid currentColor',
                            '&:focus, &:hover, &.Mui-active, &.Mui-focusVisible': {
                                boxShadow: 'inherit',
                            },
                        },
                    }}
                    />
                    <div style={{
                        position: 'relative',
                        width: '80px',
                    }}>
                        <input
                           type="number"
                           value={assumptionInputs.mepLoadWpsm}
                           onChange={onAssumptionChange('mepLoadWpsm')}
                           style={{
                               width: '100%',
                               padding: '4px 8px',
                               borderRadius: '6px',
                               border: '1px solid var(--ob-color-border-premium)',
                               textAlign: 'right',
                               fontSize: '0.875rem',
                               fontWeight: 600
                           }}
                        />
                        <span style={{
                            position: 'absolute',
                            right: '30px', // Adjust based on input width/padding
                            top: '50%',
                            transform: 'translateY(-50%)',
                            color: 'var(--ob-color-text-muted)',
                            fontSize: '0.75rem',
                            pointerEvents: 'none',
                            display: 'none' // Hidden for now as it overlaps with number
                        }}>W/m²</span>
                    </div>
                </div>
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '4px' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--ob-color-text-muted)' }}>W/m²</span>
                </div>
            </div>
          </div>

          <button
            type="button"
            className="feasibility-assumptions__reset"
            onClick={onResetAssumptions}
            style={{ marginTop: '1rem' }}
          >
             {t('wizard.assumptions.reset')}
          </button>
        </AccordionDetails>
      </Accordion>
    </section>
  )
}
