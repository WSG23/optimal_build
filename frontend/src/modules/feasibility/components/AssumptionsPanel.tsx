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
      <h3 className="feasibility-section__title">Assumptions</h3>
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
            borderColor: 'var(--ob-color-border-default)',
          },
        }}
      >
        <AccordionSummary
          expandIcon={
            <ExpandMore sx={{ color: 'var(--ob-color-text-muted)' }} />
          }
          sx={{
            padding: 'var(--ob-space-050)',
            '& .MuiAccordionSummary-content': { margin: 0 },
          }}
        >
          <header>
            <h2 className="assumptions-panel__heading">Design Parameters</h2>
          </header>
        </AccordionSummary>

        <AccordionDetails
          sx={{ padding: '0 var(--ob-space-050) var(--ob-space-075)' }}
        >
          <div className="feasibility-assumptions__grid">
            {/* Land Use Dropdown (Moved from AddressForm) */}
            {landUseInput !== undefined && onLandUseChange && (
              <div className="assumptions-panel__control-group assumptions-panel__control-group--mb">
                <label className="assumptions-panel__label">
                  {t('wizard.form.landUseLabel') || 'Land Use'}
                </label>
                <div className="assumptions-panel__select-wrapper">
                  <select
                    value={landUseInput}
                    onChange={onLandUseChange}
                    className="assumptions-panel__select"
                  >
                    <option value="Residential">Residential</option>
                    <option value="Commercial">Commercial</option>
                    <option value="Mixed Use">Mixed Use</option>
                    <option value="Industrial">Industrial</option>
                  </select>
                  <ExpandMore className="assumptions-panel__select-icon" />
                </div>
              </div>
            )}

            {/* Floor to Floor */}
            <div className="assumptions-panel__control-group assumptions-panel__control-group--mb">
              <div className="assumptions-panel__control-header">
                <label
                  htmlFor="assumption-floor"
                  className="assumptions-panel__label"
                >
                  {t('wizard.assumptions.fields.typFloorToFloor.label')}
                </label>
                <div className="assumptions-panel__input-wrapper">
                  <input
                    type="number"
                    value={assumptionInputs.typFloorToFloorM}
                    onChange={onAssumptionChange('typFloorToFloorM')}
                    min={2.5}
                    max={6.0}
                    step={0.1}
                    className="assumptions-panel__input assumptions-panel__input--cyan"
                  />
                  <span className="assumptions-panel__input-unit">m</span>
                </div>
              </div>
              <TunerSlider
                value={Number(assumptionInputs.typFloorToFloorM) || 3.0}
                onChange={handleSliderChange('typFloorToFloorM')}
                min={2.5}
                max={6.0}
                step={0.1}
                sx={{
                  color: 'var(--ob-color-brand-primary)',
                }}
              />
              <p className="assumptions-panel__hint">
                {t('wizard.assumptions.fields.typFloorToFloor.hint', {
                  value: decimalFormatter.format(
                    DEFAULT_ASSUMPTIONS.typFloorToFloorM,
                  ),
                })}
              </p>
              {renderAssumptionError('typFloorToFloorM')}
            </div>

            {/* Efficiency */}
            <div className="assumptions-panel__control-group">
              <div className="assumptions-panel__control-header">
                <label
                  htmlFor="assumption-efficiency"
                  className="assumptions-panel__label"
                >
                  {t('wizard.assumptions.fields.efficiency.label')}
                </label>
                <div className="assumptions-panel__input-wrapper">
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
                    className="assumptions-panel__input assumptions-panel__input--cyan assumptions-panel__input--narrow"
                  />
                  <span className="assumptions-panel__input-unit">%</span>
                </div>
              </div>

              <TunerSlider
                value={Number(assumptionInputs.efficiencyRatio) || 0.8}
                onChange={handleSliderChange('efficiencyRatio')}
                min={0.5}
                max={0.95}
                step={0.01}
                sx={{
                  color: 'var(--ob-color-brand-primary)',
                }}
              />

              <p className="assumptions-panel__hint">
                {t('wizard.assumptions.fields.efficiency.hint', {
                  value: decimalFormatter.format(
                    DEFAULT_ASSUMPTIONS.efficiencyRatio,
                  ),
                })}
              </p>
              {renderAssumptionError('efficiencyRatio')}
            </div>

            {/* Engineering Divider */}
            <div className="assumptions-panel__divider" />

            <h3 className="assumptions-panel__section-title">
              {t('wizard.assumptions.engineering.title') ||
                'Engineering Constraints'}
            </h3>

            {/* Structure Type */}
            <div className="assumptions-panel__control-group assumptions-panel__control-group--mb">
              <label className="assumptions-panel__label">
                {t('wizard.assumptions.fields.structure.label') ||
                  'Structural Material'}
              </label>
              <div className="assumptions-panel__card-grid">
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
            <div className="assumptions-panel__control-group">
              <div className="assumptions-panel__control-header">
                <label className="assumptions-panel__label">MEP LOAD</label>
              </div>

              <div className="assumptions-panel__slider-row">
                <TunerSlider
                  value={Number(assumptionInputs.mepLoadWpsm) || 150}
                  onChange={handleSliderChange('mepLoadWpsm')}
                  min={50}
                  max={500}
                  step={10}
                  sx={{ flex: 1 }}
                />
                <div className="assumptions-panel__input-wrapper assumptions-panel__input-wrapper--fixed">
                  <input
                    type="number"
                    value={assumptionInputs.mepLoadWpsm}
                    onChange={onAssumptionChange('mepLoadWpsm')}
                    className="assumptions-panel__input"
                  />
                </div>
              </div>
              <div className="assumptions-panel__unit-label">
                <span>W/m²</span>
              </div>
            </div>
          </div>

          <button
            type="button"
            className="feasibility-assumptions__reset"
            onClick={onResetAssumptions}
          >
            {t('wizard.assumptions.reset')}
          </button>
        </AccordionDetails>
      </Accordion>
    </section>
  )
}
