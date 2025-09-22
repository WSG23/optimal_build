import type { ChangeEvent, FormEvent } from 'react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { fetchBuildable, type BuildableResponse } from '../../api/buildable'
import { useTranslation } from '../../i18n'

const DEFAULT_ASSUMPTIONS = {
  typFloorToFloorM: 3.4,
  efficiencyRatio: 0.8,
} as const

const DEBOUNCE_MS = 300

interface AssumptionInputs {
  typFloorToFloorM: string
  efficiencyRatio: string
}

interface AssumptionErrors {
  typFloorToFloorM?: 'required' | 'invalid'
  efficiencyRatio?: 'required' | 'invalid' | 'range'
}

type WizardStatus = 'idle' | 'loading' | 'success' | 'partial' | 'empty' | 'error'

type PendingPayload = {
  address: string
  typFloorToFloorM: number
  efficiencyRatio: number
}

function anonymiseAddress(address: string): string {
  const trimmed = address.trim()
  if (!trimmed) {
    return ''
  }
  if (trimmed.length <= 5) {
    return `${trimmed[0] ?? ''}***`
  }
  const prefix = trimmed.slice(0, 3)
  const suffix = trimmed.slice(-2)
  return `${prefix}…${suffix}`
}

export function FeasibilityWizard() {
  const { t, i18n } = useTranslation()
  const [addressInput, setAddressInput] = useState('')
  const [addressError, setAddressError] = useState<string | null>(null)
  const [assumptionInputs, setAssumptionInputs] = useState<AssumptionInputs>(() => ({
    typFloorToFloorM: DEFAULT_ASSUMPTIONS.typFloorToFloorM.toString(),
    efficiencyRatio: DEFAULT_ASSUMPTIONS.efficiencyRatio.toString(),
  }))
  const [assumptionErrors, setAssumptionErrors] = useState<AssumptionErrors>({})
  const [appliedAssumptions, setAppliedAssumptions] = useState({ ...DEFAULT_ASSUMPTIONS })
  const [payload, setPayload] = useState<PendingPayload | null>(null)
  const [result, setResult] = useState<BuildableResponse | null>(null)
  const [status, setStatus] = useState<WizardStatus>('idle')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [liveAnnouncement, setLiveAnnouncement] = useState('')
  const [copyState, setCopyState] = useState<'idle' | 'copied' | 'error'>('idle')

  const abortControllerRef = useRef<AbortController | null>(null)
  const debounceRef = useRef<number | null>(null)
  const copyResetRef = useRef<number | null>(null)

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort()
      if (debounceRef.current !== null) {
        clearTimeout(debounceRef.current)
      }
      if (copyResetRef.current !== null) {
        clearTimeout(copyResetRef.current)
      }
    }
  }, [])

  const numberFormatter = useMemo(
    () =>
      new Intl.NumberFormat(i18n.language, {
        maximumFractionDigits: 0,
      }),
    [i18n.language],
  )

  const decimalFormatter = useMemo(
    () =>
      new Intl.NumberFormat(i18n.language, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }),
    [i18n.language],
  )

  const dispatchTelemetry = useCallback(
    (
      durationMs: number,
      outcome: 'success' | 'error',
      zoneCode: string | null,
      address: string,
    ) => {
      const detail = {
        event: 'feasibility.compute',
        durationMs,
        status: outcome,
        zoneCode,
        addressPreview: anonymiseAddress(address),
      }
      window.dispatchEvent(new CustomEvent('feasibility.compute', { detail }))
    },
    [],
  )

  useEffect(() => {
    if (!payload) {
      return () => {}
    }

    if (debounceRef.current !== null) {
      clearTimeout(debounceRef.current)
    }
    abortControllerRef.current?.abort()
    const controller = new AbortController()
    abortControllerRef.current = controller

    setStatus('loading')
    setErrorMessage(null)

    const startTime = typeof performance !== 'undefined' ? performance.now() : Date.now()

    debounceRef.current = window.setTimeout(() => {
      fetchBuildable(payload, { signal: controller.signal })
        .then((response) => {
          const duration =
            (typeof performance !== 'undefined' ? performance.now() : Date.now()) - startTime

          dispatchTelemetry(duration, 'success', response.zoneCode, payload.address)
          setResult(response)

          if (!response.zoneCode) {
            setStatus('empty')
            setLiveAnnouncement(t('wizard.accessibility.noZone'))
            return
          }

          if (response.rules.length === 0) {
            setStatus('partial')
          } else {
            setStatus('success')
          }

          setLiveAnnouncement(
            t('wizard.accessibility.updated', {
              zone: response.zoneCode,
              overlays: response.overlays.length,
            }),
          )
        })
        .catch((error) => {
          if (error instanceof DOMException && error.name === 'AbortError') {
            return
          }
          const duration =
            (typeof performance !== 'undefined' ? performance.now() : Date.now()) - startTime
          dispatchTelemetry(duration, 'error', null, payload.address)
          setStatus('error')
          setErrorMessage(
            error instanceof Error ? error.message : t('wizard.errors.generic'),
          )
        })
        .finally(() => {
          debounceRef.current = null
        })
    }, DEBOUNCE_MS)

    return () => {
      controller.abort()
      if (debounceRef.current !== null) {
        clearTimeout(debounceRef.current)
        debounceRef.current = null
      }
    }
  }, [payload, dispatchTelemetry, t])

  useEffect(() => {
    setPayload((previous) => {
      if (!previous) {
        return previous
      }
      if (
        previous.typFloorToFloorM === appliedAssumptions.typFloorToFloorM &&
        previous.efficiencyRatio === appliedAssumptions.efficiencyRatio
      ) {
        return previous
      }
      return {
        ...previous,
        typFloorToFloorM: appliedAssumptions.typFloorToFloorM,
        efficiencyRatio: appliedAssumptions.efficiencyRatio,
      }
    })
  }, [appliedAssumptions])

  const handleAddressChange = useCallback((event: ChangeEvent<HTMLInputElement>) => {
    setAddressInput(event.target.value)
    setAddressError(null)
  }, [])

  const handleAssumptionChange = useCallback(
    (key: keyof AssumptionInputs) => (event: ChangeEvent<HTMLInputElement>) => {
      const value = event.target.value
      setAssumptionInputs((previous) => ({ ...previous, [key]: value }))
      setAssumptionErrors((previous) => ({ ...previous, [key]: undefined }))

      if (!value.trim()) {
        setAssumptionErrors((previous) => ({ ...previous, [key]: 'required' }))
        return
      }

      const numeric = Number.parseFloat(value)
      if (!Number.isFinite(numeric) || numeric <= 0) {
        setAssumptionErrors((previous) => ({ ...previous, [key]: 'invalid' }))
        return
      }

      if (key === 'efficiencyRatio' && (numeric <= 0 || numeric > 1)) {
        setAssumptionErrors((previous) => ({ ...previous, [key]: 'range' }))
        return
      }

      setAppliedAssumptions((previous) => {
        if (previous[key] === numeric) {
          return previous
        }
        return {
          ...previous,
          [key]: numeric,
        }
      })
    },
    [],
  )

  const handleResetAssumptions = useCallback(() => {
    setAssumptionInputs({
      typFloorToFloorM: DEFAULT_ASSUMPTIONS.typFloorToFloorM.toString(),
      efficiencyRatio: DEFAULT_ASSUMPTIONS.efficiencyRatio.toString(),
    })
    setAssumptionErrors({})
    setAppliedAssumptions({ ...DEFAULT_ASSUMPTIONS })
  }, [])

  const handleSubmit = useCallback(
    (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault()
      const trimmed = addressInput.trim()
      if (!trimmed) {
        setAddressError(t('wizard.form.errors.addressRequired'))
        setStatus('idle')
        setResult(null)
        setErrorMessage(null)
        setPayload(null)
        return
      }

      setAddressError(null)
      setPayload({
        address: trimmed,
        typFloorToFloorM: appliedAssumptions.typFloorToFloorM,
        efficiencyRatio: appliedAssumptions.efficiencyRatio,
      })
    },
    [addressInput, appliedAssumptions, t],
  )

  const handleCopyRequest = useCallback(() => {
    if (!payload) {
      return
    }
    if (copyResetRef.current !== null) {
      clearTimeout(copyResetRef.current)
    }
    const body = {
      address: payload.address,
      typFloorToFloorM: payload.typFloorToFloorM,
      efficiencyRatio: payload.efficiencyRatio,
    }
    const text = `${JSON.stringify(body, null, 2)}\n`

    const copyPromise = navigator.clipboard
      ? navigator.clipboard.writeText(text)
      : Promise.reject(new Error('Clipboard API unavailable'))

    copyPromise
      .then(() => {
        setCopyState('copied')
      })
      .catch(() => {
        setCopyState('error')
      })
      .finally(() => {
        copyResetRef.current = window.setTimeout(() => {
          setCopyState('idle')
        }, 2000)
      })
  }, [payload])

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

  const renderProvenanceBadge = (provenance: BuildableResponse['rules'][number]['provenance']) => {
    if (provenance.documentId && provenance.pages && provenance.pages.length > 0) {
      return (
        <span className="feasibility-citation__badge">
          {t('wizard.citations.documentWithPages', {
            id: provenance.documentId,
            pages: provenance.pages.join(', '),
          })}
        </span>
      )
    }
    if (provenance.documentId) {
      return (
        <span className="feasibility-citation__badge">
          {t('wizard.citations.document', { id: provenance.documentId })}
        </span>
      )
    }
    if (provenance.seedTag) {
      return (
        <span className="feasibility-citation__badge">
          {t('wizard.citations.seedTag', { tag: provenance.seedTag })}
        </span>
      )
    }
    return null
  }

  const metricsView = useMemo(() => {
    if (!result) {
      return null
    }
    const metrics = [
      {
        key: 'gfaCapM2',
        label: t('wizard.results.metrics.gfaCap'),
        value: numberFormatter.format(result.metrics.gfaCapM2),
        testId: 'metric-gfa',
      },
      {
        key: 'floorsMax',
        label: t('wizard.results.metrics.floorsMax'),
        value: numberFormatter.format(result.metrics.floorsMax),
        testId: 'metric-floors',
      },
      {
        key: 'footprintM2',
        label: t('wizard.results.metrics.footprint'),
        value: numberFormatter.format(result.metrics.footprintM2),
        testId: 'metric-footprint',
      },
      {
        key: 'nsaEstM2',
        label: t('wizard.results.metrics.nsa'),
        value: numberFormatter.format(result.metrics.nsaEstM2),
        testId: 'metric-nsa',
      },
    ]
    return (
      <dl className="feasibility-metrics">
        {metrics.map((metric) => (
          <div key={metric.key} className="feasibility-metrics__item">
            <dt>{metric.label}</dt>
            <dd data-testid={metric.testId}>{metric.value}</dd>
          </div>
        ))}
      </dl>
    )
  }, [numberFormatter, result, t])

  return (
    <div className="feasibility-wizard" data-testid="feasibility-wizard">
      <header className="feasibility-wizard__header">
        <div>
          <h1>{t('wizard.title')}</h1>
          <p>{t('wizard.description')}</p>
        </div>
        <div className="feasibility-wizard__toolbar">
          <button
            type="button"
            onClick={handleCopyRequest}
            disabled={!payload}
            className="feasibility-wizard__copy"
          >
            {t('wizard.form.copyRequest')}
          </button>
          {copyState === 'copied' && (
            <span className="feasibility-wizard__copy-status" role="status">
              {t('wizard.form.copySuccess')}
            </span>
          )}
          {copyState === 'error' && (
            <span className="feasibility-wizard__copy-status" role="status">
              {t('wizard.form.copyError')}
            </span>
          )}
        </div>
      </header>

      <div className="feasibility-wizard__layout">
        <section className="feasibility-wizard__controls">
          <form className="feasibility-form" onSubmit={handleSubmit} noValidate>
            <label className="feasibility-form__label" htmlFor="address-input">
              {t('wizard.form.addressLabel')}
            </label>
            <div className="feasibility-form__field">
              <input
                id="address-input"
                name="address"
                type="text"
                value={addressInput}
                onChange={handleAddressChange}
                placeholder={t('wizard.form.addressPlaceholder')}
              />
              {addressError && <p className="feasibility-form__error">{addressError}</p>}
            </div>
            <div className="feasibility-form__actions">
              <button type="submit" className="feasibility-form__submit">
                {status === 'loading'
                  ? t('wizard.form.submitLoading')
                  : t('wizard.form.submitLabel')}
              </button>
            </div>
          </form>

          <section className="feasibility-assumptions">
            <header>
              <h2>{t('wizard.assumptions.title')}</h2>
              <p>{t('wizard.assumptions.subtitle')}</p>
            </header>
            <div className="feasibility-assumptions__grid">
              <div>
                <label htmlFor="assumption-floor">
                  {t('wizard.assumptions.fields.typFloorToFloor.label')}
                </label>
                <input
                  id="assumption-floor"
                  type="number"
                  step="0.1"
                  min={0}
                  value={assumptionInputs.typFloorToFloorM}
                  onChange={handleAssumptionChange('typFloorToFloorM')}
                />
                <p className="feasibility-assumptions__hint">
                  {t('wizard.assumptions.fields.typFloorToFloor.hint', {
                    value: decimalFormatter.format(DEFAULT_ASSUMPTIONS.typFloorToFloorM),
                  })}
                </p>
                {renderAssumptionError('typFloorToFloorM')}
              </div>
              <div>
                <label htmlFor="assumption-efficiency">
                  {t('wizard.assumptions.fields.efficiency.label')}
                </label>
                <input
                  id="assumption-efficiency"
                  type="number"
                  step="0.01"
                  min={0}
                  max={1}
                  value={assumptionInputs.efficiencyRatio}
                  onChange={handleAssumptionChange('efficiencyRatio')}
                />
                <p className="feasibility-assumptions__hint">
                  {t('wizard.assumptions.fields.efficiency.hint', {
                    value: decimalFormatter.format(DEFAULT_ASSUMPTIONS.efficiencyRatio),
                  })}
                </p>
                {renderAssumptionError('efficiencyRatio')}
              </div>
            </div>
            <button
              type="button"
              className="feasibility-assumptions__reset"
              onClick={handleResetAssumptions}
            >
              {t('wizard.assumptions.reset')}
            </button>
          </section>
        </section>

        <section className="feasibility-results" aria-live="polite" aria-busy={status === 'loading'}>
          {status === 'idle' && (
            <p className="feasibility-results__placeholder">
              {t('wizard.states.idle')}
            </p>
          )}

          {status === 'loading' && (
            <div className="feasibility-results__skeleton" role="status">
              <div className="skeleton skeleton--heading" />
              <div className="skeleton skeleton--row" />
              <div className="skeleton skeleton--row" />
              <div className="skeleton skeleton--grid" />
            </div>
          )}

          {status === 'error' && (
            <p className="feasibility-results__error" role="alert">
              {errorMessage ?? t('wizard.errors.generic')}
            </p>
          )}

          {(status === 'success' || status === 'partial' || status === 'empty') && result && (
            <div className="feasibility-results__content">
              <header className="feasibility-results__header">
                <div>
                  <span className="feasibility-results__label">{t('wizard.results.zone')}</span>
                  <span className="feasibility-results__value" data-testid="zone-code">
                    {result.zoneCode ?? t('wizard.results.zoneUnknown')}
                  </span>
                </div>
                <div>
                  <span className="feasibility-results__label">{t('wizard.results.overlays')}</span>
                  <div className="feasibility-results__overlays" data-testid="overlay-badges">
                    {result.overlays.length === 0 && (
                      <span className="feasibility-results__badge">
                        {t('wizard.results.none')}
                      </span>
                    )}
                    {result.overlays.map((overlay) => (
                      <span key={overlay} className="feasibility-results__badge">
                        {overlay}
                      </span>
                    ))}
                  </div>
                </div>
              </header>

              {metricsView}

              {status === 'empty' && (
                <p className="feasibility-results__empty">{t('wizard.states.empty')}</p>
              )}

              {status === 'partial' && result.zoneCode && (
                <p className="feasibility-results__partial">{t('wizard.states.partial')}</p>
              )}

              {result.rules.length > 0 && (
                <section className="feasibility-citations">
                  <h3>{t('wizard.citations.title')}</h3>
                  <ul>
                    {result.rules.map((rule) => (
                      <li key={rule.id} className="feasibility-citation">
                        <div className="feasibility-citation__meta">
                          <span className="feasibility-citation__authority">{rule.authority}</span>
                          <span className="feasibility-citation__clause">
                            {rule.provenance.clauseRef ?? t('wizard.citations.unknownClause')}
                          </span>
                        </div>
                        <p className="feasibility-citation__parameter">
                          {`${rule.parameterKey} ${rule.operator} ${rule.value}${rule.unit ? ` ${rule.unit}` : ''}`}
                        </p>
                        {renderProvenanceBadge(rule.provenance)}
                      </li>
                    ))}
                  </ul>
                </section>
              )}
            </div>
          )}
        </section>
      </div>

      <div className="sr-only" aria-live="polite">
        {liveAnnouncement}
      </div>
    </div>
  )
}

export default FeasibilityWizard
