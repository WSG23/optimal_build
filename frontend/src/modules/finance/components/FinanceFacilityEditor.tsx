import { useEffect, useMemo, useState } from 'react'

import type {
  ConstructionLoanInput,
  ConstructionLoanFacilityInput,
  FinanceScenarioSummary,
} from '../../../api/finance'
import { useTranslation } from '../../../i18n'

interface FinanceFacilityEditorProps {
  scenario: FinanceScenarioSummary | null
  saving: boolean
  onSave: (input: ConstructionLoanInput) => Promise<void>
}

type FacilityFormState = {
  id: string
  name: string
  amount: string
  interestRate: string
  periodsPerYear: string
  capitaliseInterest: boolean
  upfrontFeePct: string
  exitFeePct: string
  reserveMonths: string
  amortisationMonths: string
  metadata?: Record<string, unknown> | null
}

type LoanFormState = {
  interestRate: string
  periodsPerYear: string
  capitaliseInterest: boolean
  facilities: FacilityFormState[]
}

const DEFAULT_PERIODS = '12'

function toFacilityFormState(
  facility: ConstructionLoanFacilityInput,
  index: number,
): FacilityFormState {
  return {
    id: `facility-${Date.now()}-${index}`,
    name: facility.name ?? '',
    amount: facility.amount ?? '',
    interestRate: facility.interestRate ?? '',
    periodsPerYear:
      facility.periodsPerYear !== undefined && facility.periodsPerYear !== null
        ? String(facility.periodsPerYear)
        : '',
    capitaliseInterest:
      facility.capitaliseInterest === undefined
        ? true
        : Boolean(facility.capitaliseInterest),
    upfrontFeePct: facility.upfrontFeePct ?? '',
    exitFeePct: facility.exitFeePct ?? '',
    reserveMonths:
      facility.reserveMonths !== undefined && facility.reserveMonths !== null
        ? String(facility.reserveMonths)
        : '',
    amortisationMonths:
      facility.amortisationMonths !== undefined &&
      facility.amortisationMonths !== null
        ? String(facility.amortisationMonths)
        : '',
    metadata: facility.metadata ?? null,
  }
}

function buildInitialState(
  scenario: FinanceScenarioSummary | null,
): LoanFormState {
  const config = scenario?.constructionLoan
  if (!config) {
    return {
      interestRate: '',
      periodsPerYear: DEFAULT_PERIODS,
      capitaliseInterest: true,
      facilities: [],
    }
  }

  const facilities =
    config.facilities?.map((facility, index) =>
      toFacilityFormState(facility, index),
    ) ?? []

  return {
    interestRate: config.interestRate ?? '',
    periodsPerYear:
      config.periodsPerYear !== undefined && config.periodsPerYear !== null
        ? String(config.periodsPerYear)
        : DEFAULT_PERIODS,
    capitaliseInterest:
      config.capitaliseInterest === undefined
        ? true
        : Boolean(config.capitaliseInterest),
    facilities,
  }
}

export function FinanceFacilityEditor({
  scenario,
  saving,
  onSave,
}: FinanceFacilityEditorProps) {
  const { t } = useTranslation()
  const [form, setForm] = useState<LoanFormState>(() =>
    buildInitialState(scenario),
  )
  const [initial, setInitial] = useState<LoanFormState>(() =>
    buildInitialState(scenario),
  )

  useEffect(() => {
    const nextState = buildInitialState(scenario)
    setForm(nextState)
    setInitial(nextState)
  }, [scenario, scenario?.scenarioId])

  const hasFacilities = form.facilities.length > 0
  const canSave = useMemo(() => {
    if (!form.interestRate.trim()) {
      return false
    }
    if (!hasFacilities) {
      return false
    }
    return form.facilities.every(
      (facility) =>
        facility.name.trim() &&
        facility.amount.trim() &&
        facility.interestRate.trim(),
    )
  }, [form, hasFacilities])

  const handleBaseFieldChange = (
    key: 'interestRate' | 'periodsPerYear' | 'capitaliseInterest',
    value: string | boolean,
  ) => {
    setForm((prev) => ({
      ...prev,
      [key]: value,
    }))
  }

  const handleFacilityChange = (
    id: string,
    key:
      | 'name'
      | 'amount'
      | 'interestRate'
      | 'periodsPerYear'
      | 'upfrontFeePct'
      | 'exitFeePct'
      | 'reserveMonths'
      | 'amortisationMonths',
    value: string,
  ) => {
    setForm((prev) => ({
      ...prev,
      facilities: prev.facilities.map((facility) =>
        facility.id === id ? { ...facility, [key]: value } : facility,
      ),
    }))
  }

  const handleFacilityCapitaliseToggle = (id: string, value: boolean) => {
    setForm((prev) => ({
      ...prev,
      facilities: prev.facilities.map((facility) =>
        facility.id === id
          ? { ...facility, capitaliseInterest: value }
          : facility,
      ),
    }))
  }

  const handleAddFacility = () => {
    setForm((prev) => ({
      ...prev,
      facilities: [
        ...prev.facilities,
        {
          id: `facility-${Date.now()}-${prev.facilities.length}`,
          name: '',
          amount: '',
          interestRate: prev.interestRate,
          periodsPerYear: prev.periodsPerYear,
          capitaliseInterest: true,
          upfrontFeePct: '',
          exitFeePct: '',
          reserveMonths: '',
          amortisationMonths: '',
          metadata: null,
        },
      ],
    }))
  }

  const handleRemoveFacility = (id: string) => {
    setForm((prev) => ({
      ...prev,
      facilities: prev.facilities.filter((facility) => facility.id !== id),
    }))
  }

  const handleReset = () => {
    setForm(initial)
  }

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!canSave || !scenario) {
      return
    }
    const periods = form.periodsPerYear.trim()
    const payload: ConstructionLoanInput = {
      interestRate: form.interestRate.trim(),
      periodsPerYear: periods ? Number(periods) : undefined,
      capitaliseInterest: form.capitaliseInterest,
      facilities: form.facilities.map((facility, index) => {
        const facilityPeriods = facility.periodsPerYear.trim()
        const reserveMonths = facility.reserveMonths.trim()
        const amortisationMonths = facility.amortisationMonths.trim()
        const facilityPayload: ConstructionLoanFacilityInput = {
          name: facility.name.trim() || `Facility ${index + 1}`,
          amount: facility.amount.trim(),
          interestRate:
            facility.interestRate.trim() || form.interestRate.trim(),
          periodsPerYear: facilityPeriods
            ? Number(facilityPeriods)
            : undefined,
          capitaliseInterest: facility.capitaliseInterest,
          upfrontFeePct: facility.upfrontFeePct.trim()
            ? facility.upfrontFeePct.trim()
            : null,
          exitFeePct: facility.exitFeePct.trim()
            ? facility.exitFeePct.trim()
            : null,
          reserveMonths: reserveMonths ? Number(reserveMonths) : undefined,
          amortisationMonths: amortisationMonths
            ? Number(amortisationMonths)
            : undefined,
          metadata: facility.metadata ?? undefined,
        }
        return facilityPayload
      }),
    }
    await onSave(payload)
  }

  if (!scenario) {
    return null
  }

  return (
    <section className="finance-facility-editor">
      <header className="finance-facility-editor__header">
        <h2>{t('finance.facilityEditor.title')}</h2>
        <p>{t('finance.facilityEditor.description')}</p>
      </header>
      <form className="finance-facility-editor__form" onSubmit={handleSubmit}>
        <div className="finance-facility-editor__base-grid">
          <label className="finance-facility-editor__field">
            <span>{t('finance.facilityEditor.base.rate')}</span>
            <input
              type="number"
              step="0.0001"
              value={form.interestRate}
              onChange={(event) =>
                handleBaseFieldChange('interestRate', event.target.value)
              }
            />
          </label>
          <label className="finance-facility-editor__field">
            <span>{t('finance.facilityEditor.base.periods')}</span>
            <input
              type="number"
              min={1}
              value={form.periodsPerYear}
              onChange={(event) =>
                handleBaseFieldChange('periodsPerYear', event.target.value)
              }
            />
          </label>
          <label className="finance-facility-editor__checkbox">
            <input
              type="checkbox"
              checked={form.capitaliseInterest}
              onChange={(event) =>
                handleBaseFieldChange(
                  'capitaliseInterest',
                  event.target.checked,
                )
              }
            />
            <span>{t('finance.facilityEditor.base.capitalised')}</span>
          </label>
        </div>

        <div className="finance-facility-editor__table-wrapper">
          <table className="finance-facility-editor__table">
            <caption className="finance-facility-editor__caption">
              {t('finance.facilityEditor.table.caption')}
            </caption>
            <thead>
              <tr>
                <th scope="col">
                  {t('finance.facilityEditor.table.headers.name')}
                </th>
                <th scope="col">
                  {t('finance.facilityEditor.table.headers.amount')}
                </th>
                <th scope="col">
                  {t('finance.facilityEditor.table.headers.rate')}
                </th>
                <th scope="col">
                  {t('finance.facilityEditor.table.headers.periods')}
                </th>
                <th scope="col">
                  {t('finance.facilityEditor.table.headers.capitalised')}
                </th>
                <th scope="col">
                  {t('finance.facilityEditor.table.headers.upfront')}
                </th>
                <th scope="col">
                  {t('finance.facilityEditor.table.headers.exit')}
                </th>
                <th scope="col" />
              </tr>
            </thead>
            <tbody>
              {form.facilities.length === 0 ? (
                <tr>
                  <td colSpan={8}>
                    {t('finance.facilityEditor.empty')}
                  </td>
                </tr>
              ) : (
                form.facilities.map((facility) => (
                  <tr key={facility.id}>
                    <td>
                      <input
                        type="text"
                        value={facility.name}
                        onChange={(event) =>
                          handleFacilityChange(
                            facility.id,
                            'name',
                            event.target.value,
                          )
                        }
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        step="0.01"
                        value={facility.amount}
                        onChange={(event) =>
                          handleFacilityChange(
                            facility.id,
                            'amount',
                            event.target.value,
                          )
                        }
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        step="0.0001"
                        value={facility.interestRate}
                        onChange={(event) =>
                          handleFacilityChange(
                            facility.id,
                            'interestRate',
                            event.target.value,
                          )
                        }
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        min={1}
                        value={facility.periodsPerYear}
                        onChange={(event) =>
                          handleFacilityChange(
                            facility.id,
                            'periodsPerYear',
                            event.target.value,
                          )
                        }
                      />
                    </td>
                    <td className="finance-facility-editor__checkbox-cell">
                      <input
                        type="checkbox"
                        checked={facility.capitaliseInterest}
                        onChange={(event) =>
                          handleFacilityCapitaliseToggle(
                            facility.id,
                            event.target.checked,
                          )
                        }
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        step="0.01"
                        value={facility.upfrontFeePct}
                        onChange={(event) =>
                          handleFacilityChange(
                            facility.id,
                            'upfrontFeePct',
                            event.target.value,
                          )
                        }
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        step="0.01"
                        value={facility.exitFeePct}
                        onChange={(event) =>
                          handleFacilityChange(
                            facility.id,
                            'exitFeePct',
                            event.target.value,
                          )
                        }
                      />
                    </td>
                    <td className="finance-facility-editor__actions">
                      <button
                        type="button"
                        className="finance-facility-editor__remove"
                        onClick={() => handleRemoveFacility(facility.id)}
                      >
                        {t('finance.facilityEditor.actions.remove')}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="finance-facility-editor__actions-row">
          <button
            type="button"
            className="finance-facility-editor__add"
            onClick={handleAddFacility}
            disabled={saving}
          >
            {t('finance.facilityEditor.actions.add')}
          </button>
          <div className="finance-facility-editor__action-buttons">
            <button
              type="button"
              className="finance-facility-editor__reset"
              onClick={handleReset}
              disabled={saving}
            >
              {t('finance.facilityEditor.actions.reset')}
            </button>
            <button
              type="submit"
              className="finance-facility-editor__save"
              disabled={!canSave || saving}
            >
              {saving
                ? t('finance.facilityEditor.actions.saving')
                : t('finance.facilityEditor.actions.save')}
            </button>
          </div>
        </div>
      </form>
    </section>
  )
}
