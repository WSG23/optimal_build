import { ExpandMore } from '@mui/icons-material'
import { Accordion, AccordionDetails, AccordionSummary } from '@mui/material'
import type { ChangeEvent } from 'react'
import { useState } from 'react'

import { HolographicCard } from './HolographicCard'
import { TunerSlider } from './TunerSlider'
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
  landUseInput?: string
  onLandUseChange?: (event: ChangeEvent<HTMLSelectElement>) => void
}

export function AssumptionsPanel({
  assumptionInputs,
  assumptionErrors,
  decimalFormatter,
  onAssumptionChange,
  onResetAssumptions,
  t,
  landUseInput,
  onLandUseChange,
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
        onChange={() => {
          setExpanded(!expanded)
        }}
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
            borderColor: 'rgba(0,0,0,0.12)',
          },
        }}
      >
        <AccordionSummary
          expandIcon={
            <ExpandMore sx={{ color: 'var(--ob-color-text-muted)' }} />
          }
          sx={{
            padding: 'var(--ob-space-4)',
            '& .MuiAccordionSummary-content': { margin: 0 },
          }}
        >
          <header>
            <h2 className="text-heading" style={{ margin: 0 }}>
              {t('wizard.assumptions.title') || 'Design Parameters'}
            </h2>
            <p
              style={{
                margin: '4px 0 0',
                fontSize: '0.875rem',
                color: 'var(--ob-color-text-muted)',
              }}
            >
              {/* FIXED: Replaced raw string with concise label */}
              Design Parameters
            </p>
          </header>
        </AccordionSummary>

        <AccordionDetails
          sx={{ padding: '0 var(--ob-space-4) var(--ob-space-6)' }}
        >
          <div className="feasibility-assumptions__grid">
            {/* Land Use Dropdown (Moved from AddressForm) */}
            {landUseInput !== undefined && onLandUseChange && (
              <div
                className="feasibility-control-group"
                style={{ marginBottom: 'var(--ob-space-6)' }}
              >
                <label
                  style={{
                    color: 'rgba(255,255,255,0.9)',
                    fontWeight: 600,
                    fontSize: '0.9rem',
                    marginBottom: '8px',
                    display: 'block',
                  }}
                >
                  {t('wizard.form.landUseLabel') || 'Land Use'}
                </label>
                <div style={{ position: 'relative' }}>
                  <select
                    value={landUseInput}
                    onChange={onLandUseChange}
                    style={{
                      width: '100%',
                      padding: '10px 12px',
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      borderRadius: '6px',
                      color: 'white',
                      fontSize: '0.9rem',
                      outline: 'none',
                      appearance: 'none',
                      cursor: 'pointer',
                    }}
                  >
                    <option value="Residential" style={{ color: 'black' }}>
                      Residential
                    </option>
                    <option value="Commercial" style={{ color: 'black' }}>
                      Commercial
                    </option>
                    <option value="Mixed Use" style={{ color: 'black' }}>
                      Mixed Use
                    </option>
                    <option value="Industrial" style={{ color: 'black' }}>
                      Industrial
                    </option>
                  </select>
                  <ExpandMore
                    sx={{
                      position: 'absolute',
                      right: '10px',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      pointerEvents: 'none',
                      color: 'rgba(255,255,255,0.5)',
                    }}
                  />
                </div>
              </div>
            )}

            {/* Floor to Floor */}
            <div
              className="feasibility-control-group"
              style={{ marginBottom: 'var(--ob-space-6)' }}
            >
              <div
                className="feasibility-control-group-header"
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '8px',
                }}
              >
                <label
                  htmlFor="assumption-floor"
                  style={{
                    color: 'rgba(255,255,255,0.9)',
                    fontWeight: 500,
                    fontSize: '0.9rem',
                  }}
                >
                  {t('wizard.assumptions.fields.typFloorToFloor.label')}
                </label>
                <div style={{ position: 'relative' }}>
                  <input
                    type="number"
                    value={assumptionInputs.typFloorToFloorM}
                    onChange={onAssumptionChange('typFloorToFloorM')}
                    min={2.5}
                    max={6.0}
                    step={0.1}
                    style={{
                      width: '60px',
                      padding: '4px 24px 4px 8px',
                      background: 'rgba(6, 182, 212, 0.1)',
                      border: '1px solid rgba(6, 182, 212, 0.3)',
                      borderRadius: '6px',
                      color: '#06b6d4',
                      fontFamily: 'monospace',
                      fontWeight: 700,
                      fontSize: '0.875rem',
                      textAlign: 'right',
                      outline: 'none',
                    }}
                  />
                  <span
                    style={{
                      position: 'absolute',
                      right: '8px',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      color: 'rgba(6, 182, 212, 0.7)',
                      fontSize: '0.75rem',
                      pointerEvents: 'none',
                    }}
                  >
                    m
                  </span>
                </div>
              </div>
              <TunerSlider
                value={Number(assumptionInputs.typFloorToFloorM) || 3.0}
                onChange={handleSliderChange('typFloorToFloorM')}
                min={2.5}
                max={6.0}
                step={0.1}
                sx={{
                  color: 'var(--ob-color-accent)',
                }}
              />
              <p
                className="feasibility-assumptions__hint"
                style={{
                  fontSize: '0.75rem',
                  color: 'var(--ob-color-text-muted)',
                  marginTop: '4px',
                }}
              >
                {t('wizard.assumptions.fields.typFloorToFloor.hint', {
                  value: decimalFormatter.format(
                    DEFAULT_ASSUMPTIONS.typFloorToFloorM,
                  ),
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
                  style={{
                    fontWeight: 600,
                    fontSize: '0.875rem',
                    color: 'rgba(255,255,255,0.9)',
                  }}
                >
                  {t('wizard.assumptions.fields.efficiency.label')}
                </label>
                <div style={{ position: 'relative' }}>
                  <input
                    type="number"
                    value={Math.round(
                      (Number(assumptionInputs.efficiencyRatio) || 0) * 100,
                    )}
                    onChange={(e) => {
                      const percentValue = parseFloat(e.target.value) || 0
                      const decimalValue = Math.min(
                        0.95,
                        Math.max(0.5, percentValue / 100),
                      )
                      const syntheticEvent = {
                        target: { value: decimalValue.toString() },
                      } as ChangeEvent<HTMLInputElement>
                      onAssumptionChange('efficiencyRatio')(syntheticEvent)
                    }}
                    min={50}
                    max={95}
                    step={1}
                    style={{
                      width: '56px',
                      padding: '4px 20px 4px 8px',
                      background: 'rgba(6, 182, 212, 0.1)',
                      border: '1px solid rgba(6, 182, 212, 0.3)',
                      borderRadius: '6px',
                      color: '#06b6d4',
                      fontFamily: 'monospace',
                      fontWeight: 700,
                      fontSize: '0.8125rem',
                      textAlign: 'right',
                      outline: 'none',
                    }}
                  />
                  <span
                    style={{
                      position: 'absolute',
                      right: '8px',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      color: 'rgba(6, 182, 212, 0.7)',
                      fontSize: '0.75rem',
                      pointerEvents: 'none',
                    }}
                  >
                    %
                  </span>
                </div>
              </div>

              <TunerSlider
                value={Number(assumptionInputs.efficiencyRatio) || 0.8}
                onChange={handleSliderChange('efficiencyRatio')}
                min={0.5}
                max={0.95}
                step={0.01}
                sx={{
                  color: 'var(--ob-color-accent)',
                }}
              />

              <p
                className="feasibility-assumptions__hint"
                style={{
                  fontSize: '0.75rem',
                  color: 'var(--ob-color-text-muted)',
                  marginTop: '4px',
                }}
              >
                {t('wizard.assumptions.fields.efficiency.hint', {
                  value: decimalFormatter.format(
                    DEFAULT_ASSUMPTIONS.efficiencyRatio,
                  ),
                })}
              </p>
              {renderAssumptionError('efficiencyRatio')}
            </div>

            {/* Engineering Divider */}
            <div
              style={{
                height: '1px',
                background: 'var(--ob-color-border-premium)',
                margin: 'var(--ob-space-8) 0', // Increased spacing as requested
              }}
            />

            <h3
              className="text-eyebrow"
              style={{ marginBottom: 'var(--ob-space-4)' }}
            >
              {t('wizard.assumptions.engineering.title') ||
                'Engineering Constraints'}
            </h3>

            {/* Structure Type */}
            <div
              className="feasibility-control-group"
              style={{ marginBottom: 'var(--ob-space-6)' }}
            >
              <label
                className="text-body"
                style={{
                  fontWeight: 600,
                  fontSize: '0.875rem',
                  display: 'block',
                  marginBottom: 'var(--ob-space-3)',
                  color: 'rgba(255,255,255,0.9)',
                }}
              >
                {t('wizard.assumptions.fields.structure.label') ||
                  'Structural Material'}
              </label>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(3, 1fr)',
                  gap: '12px',
                }}
              >
                {[
                  {
                    value: 'rc',
                    label: 'RC Structure',
                    fullLabel: 'Reinforced Concrete',
                    icon: '🏢',
                    cost: '$$',
                  },
                  {
                    value: 'steel',
                    label: 'Steel Frame',
                    fullLabel: 'Steel Frame Structure',
                    icon: '🏗️',
                    cost: '+15%',
                  },
                  {
                    value: 'mass_timber',
                    label: 'Mass Timber',
                    fullLabel: 'Mass Timber Structure',
                    icon: '🌲',
                    cost: '+25%',
                  },
                ].map((option) => (
                  <HolographicCard
                    key={option.value}
                    selected={assumptionInputs.structureType === option.value}
                    onClick={() => {
                      const syntheticEvent = {
                        target: { value: option.value },
                      } as ChangeEvent<HTMLInputElement>
                      onAssumptionChange('structureType')(syntheticEvent)
                    }}
                    label={option.label}
                    icon={option.icon}
                    costImpact={option.cost}
                    title={option.fullLabel}
                  />
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
                <label
                  style={{
                    fontWeight: 600,
                    fontSize: '0.875rem',
                    color: 'rgba(255,255,255,0.9)',
                  }}
                >
                  {/* FIXED: Replaced raw string with concise uppercase label */}
                  MEP LOAD
                </label>
              </div>

              <div
                style={{ display: 'flex', alignItems: 'center', gap: '16px' }}
              >
                <TunerSlider
                  value={Number(assumptionInputs.mepLoadWpsm) || 150}
                  onChange={handleSliderChange('mepLoadWpsm')}
                  min={50}
                  max={500}
                  step={10}
                  sx={{ flex: 1 }}
                />
                <div
                  style={{
                    position: 'relative',
                    width: '80px',
                  }}
                >
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
                      fontWeight: 600,
                    }}
                  />
                  <span
                    style={{
                      position: 'absolute',
                      right: '30px', // Adjust based on input width/padding
                      top: '50%',
                      transform: 'translateY(-50%)',
                      color: 'var(--ob-color-text-muted)',
                      fontSize: '0.75rem',
                      pointerEvents: 'none',
                      display: 'none', // Hidden for now as it overlaps with number
                    }}
                  >
                    W/m²
                  </span>
                </div>
              </div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'flex-end',
                  marginTop: '4px',
                }}
              >
                <span
                  style={{
                    fontSize: '0.75rem',
                    color: 'var(--ob-color-text-muted)',
                  }}
                >
                  W/m²
                </span>
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
