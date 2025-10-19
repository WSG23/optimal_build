import type { ChangeEvent, FormEvent } from 'react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { cssVar } from '../../tokens'

import { AppLayout } from '../../App'
import { fetchBuildable, type BuildableSummary } from '../../api/buildable'
import {
  generateProfessionalPack,
  type ProfessionalPackSummary,
  type ProfessionalPackType,
} from '../../api/agents'
import { useTranslation } from '../../i18n'
import { useRouterLocation } from '../../router'

type StoredAssetOptimization = {
  assetType: string
  allocationPct: number
  allocatedGfaSqm?: number | null
  niaEfficiency?: number | null
  targetFloorHeightM?: number | null
  parkingRatioPer1000Sqm?: number | null
  notes?: string[]
}

const ASSET_MIX_STORAGE_PREFIX = 'developer-asset-mix:'

const DEFAULT_ASSUMPTIONS = {
  typFloorToFloorM: 3.4,
  efficiencyRatio: 0.8,
} as const

const DEBOUNCE_MS = 300

const readCssVar = (token: string): string =>
  String((cssVar as (name: string) => unknown)(token))

interface AssumptionInputs {
  typFloorToFloorM: string
  efficiencyRatio: string
}

interface AssumptionErrors {
  typFloorToFloorM?: 'required' | 'invalid'
  efficiencyRatio?: 'required' | 'invalid' | 'range'
}

type WizardStatus =
  | 'idle'
  | 'loading'
  | 'success'
  | 'partial'
  | 'empty'
  | 'error'

type PendingPayload = {
  address: string
  typFloorToFloorM: number
  efficiencyRatio: number
}

interface PackOption {
  value: ProfessionalPackType
  labelKey: string
  descriptionKey: string
}

const PACK_OPTIONS: readonly PackOption[] = [
  {
    value: 'universal',
    labelKey: 'agentsCapture.pack.options.universal.title',
    descriptionKey: 'agentsCapture.pack.options.universal.description',
  },
  {
    value: 'investment',
    labelKey: 'agentsCapture.pack.options.investment.title',
    descriptionKey: 'agentsCapture.pack.options.investment.description',
  },
  {
    value: 'sales',
    labelKey: 'agentsCapture.pack.options.sales.title',
    descriptionKey: 'agentsCapture.pack.options.sales.description',
  },
  {
    value: 'lease',
    labelKey: 'agentsCapture.pack.options.lease.title',
    descriptionKey: 'agentsCapture.pack.options.lease.description',
  },
] as const

function formatFileSize(bytes: number | null, locale: string): string {
  if (bytes == null || Number.isNaN(bytes)) {
    return '—'
  }
  if (bytes < 1024) {
    return `${new Intl.NumberFormat(locale).format(bytes)} B`
  }
  const units = ['KB', 'MB', 'GB'] as const
  let value = bytes / 1024
  let index = 0
  while (value >= 1024 && index < units.length - 1) {
    value /= 1024
    index += 1
  }
  return `${new Intl.NumberFormat(locale, { maximumFractionDigits: 1 }).format(value)} ${units[index]}`
}

function anonymiseAddress(address: string): string {
  const trimmed = address.trim()
  if (!trimmed) {
    return ''
  }
  if (trimmed.length <= 5) {
    return `${trimmed[0]}***`
  }
  const prefix = trimmed.slice(0, 3)
  const suffix = trimmed.slice(-2)
  return `${prefix}…${suffix}`
}

interface FeasibilityWizardProps {
  generatePackFn?: typeof generateProfessionalPack
  withLayout?: boolean
}

export function FeasibilityWizard({
  generatePackFn = generateProfessionalPack,
  withLayout = true,
}: FeasibilityWizardProps = {}) {
  const { t, i18n } = useTranslation()
  const { search: routerSearch } = useRouterLocation()
  const [addressInput, setAddressInput] = useState('')
  const [addressError, setAddressError] = useState<string | null>(null)
  const [assumptionInputs, setAssumptionInputs] = useState<AssumptionInputs>(
    () => ({
      typFloorToFloorM: DEFAULT_ASSUMPTIONS.typFloorToFloorM.toString(),
      efficiencyRatio: DEFAULT_ASSUMPTIONS.efficiencyRatio.toString(),
    }),
  );
  const [assumptionErrors, setAssumptionErrors] = useState<AssumptionErrors>({})
  const [appliedAssumptions, setAppliedAssumptions] = useState({
    ...DEFAULT_ASSUMPTIONS,
  })
  const [payload, setPayload] = useState<PendingPayload | null>(null)
  const [result, setResult] = useState<BuildableSummary | null>(null)
  const [status, setStatus] = useState<WizardStatus>('idle')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [liveAnnouncement, setLiveAnnouncement] = useState('')
  const [copyState, setCopyState] = useState<'idle' | 'copied' | 'error'>(
    'idle',
  )
  const [packPropertyId, setPackPropertyId] = useState<string>('')
  const [packType, setPackType] = useState<ProfessionalPackType>('universal')
  const [packSummary, setPackSummary] = useState<ProfessionalPackSummary | null>(
    null,
  )
  const [packLoading, setPackLoading] = useState(false)
  const [packError, setPackError] = useState<string | null>(null)
const [capturedAssetMix, setCapturedAssetMix] = useState<StoredAssetOptimization[]>([])
const [capturedFinancialSummary, setCapturedFinancialSummary] = useState<{
  totalEstimatedRevenueSgd: number | null
  totalEstimatedCapexSgd: number | null
  dominantRiskProfile: string | null
  notes: string[]
} | null>(null)

  const copyStatusColor = useMemo<string>(() => {
    if (copyState === 'copied') {
      return readCssVar('color-success-strong')
    }
    if (copyState === 'error') {
      return readCssVar('color-error-strong')
    }
    return readCssVar('color-brand-primary')
  }, [copyState])

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

  const propertyIdFromQuery = useMemo(() => {
    if (!routerSearch) {
      return ''
    }
    try {
      const params = new URLSearchParams(routerSearch)
      return params.get('propertyId') ?? ''
    } catch {
      return ''
    }
  }, [routerSearch])

useEffect(() => {
  setPackPropertyId((current) =>
    current === propertyIdFromQuery ? current : propertyIdFromQuery,
  )
  setPackSummary(null)
  setPackError(null)
  setPackLoading(false)

  if (propertyIdFromQuery) {
    try {
      const raw = sessionStorage.getItem(
        `${ASSET_MIX_STORAGE_PREFIX}${propertyIdFromQuery}`,
      )
      if (raw) {
        const parsed = JSON.parse(raw) as {
          optimizations?: StoredAssetOptimization[]
          financialSummary?: {
            totalEstimatedRevenueSgd: number | null
            totalEstimatedCapexSgd: number | null
            dominantRiskProfile: string | null
            notes?: string[]
          }
        }
        if (Array.isArray(parsed.optimizations)) {
          setCapturedAssetMix(parsed.optimizations)
        } else {
          setCapturedAssetMix([])
        }
        if (parsed.financialSummary) {
          setCapturedFinancialSummary({
            totalEstimatedRevenueSgd:
              parsed.financialSummary.totalEstimatedRevenueSgd ?? null,
            totalEstimatedCapexSgd:
              parsed.financialSummary.totalEstimatedCapexSgd ?? null,
            dominantRiskProfile:
              parsed.financialSummary.dominantRiskProfile ?? null,
            notes: parsed.financialSummary.notes ?? [],
          })
        } else {
          setCapturedFinancialSummary(null)
        }
      } else {
        setCapturedAssetMix([])
        setCapturedFinancialSummary(null)
      }
    } catch (error) {
      console.warn('Unable to load stored asset mix', error)
      setCapturedAssetMix([])
      setCapturedFinancialSummary(null)
    }
  } else {
    setCapturedAssetMix([])
    setCapturedFinancialSummary(null)
  }
}, [propertyIdFromQuery])

  const selectedPackOption = useMemo(() => {
    return PACK_OPTIONS.find((option) => option.value === packType) ?? PACK_OPTIONS[0]
  }, [packType])

const numberFormatter = useMemo(
  () =>
    new Intl.NumberFormat(i18n.language, {
      maximumFractionDigits: 0,
    }),
  [i18n.language],
)

const oneDecimalFormatter = useMemo(
  () =>
    new Intl.NumberFormat(i18n.language, {
      maximumFractionDigits: 1,
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

    const startTime =
      typeof performance !== 'undefined' ? performance.now() : Date.now()

    debounceRef.current = window.setTimeout(() => {
      fetchBuildable(payload, { signal: controller.signal })
        .then((response) => {
          const duration =
            (typeof performance !== 'undefined'
              ? performance.now()
              : Date.now()) - startTime

          dispatchTelemetry(
            duration,
            'success',
            response.zoneCode,
            payload.address,
          )
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
            (typeof performance !== 'undefined'
              ? performance.now()
              : Date.now()) - startTime
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

  const handleAddressChange = useCallback(
    (event: ChangeEvent<HTMLInputElement>) => {
      setAddressInput(event.target.value)
      setAddressError(null)
    },
    [],
  )

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

    const clipboard =
      typeof navigator !== 'undefined' && 'clipboard' in navigator
        ? navigator.clipboard
        : undefined
    const copyPromise = clipboard
      ? clipboard.writeText(text)
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

  const handlePackSubmit = useCallback(
    (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault()
      const trimmed = packPropertyId.trim()
      if (!trimmed) {
        setPackError(t('wizard.pack.missingProperty'))
        setPackSummary(null)
        return
      }

      setPackLoading(true)
      setPackError(null)

      Promise.resolve(generatePackFn(trimmed, packType))
        .then((summary) => {
          setPackSummary(summary)
        })
        .catch((error) => {
          setPackSummary(null)
          setPackError(
            error instanceof Error
              ? error.message
              : t('wizard.pack.errorFallback'),
          )
        })
        .finally(() => {
          setPackLoading(false)
        })
    },
    [generatePackFn, packPropertyId, packType, t],
  )

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

  const renderProvenanceBadge = (
    provenance: BuildableSummary['rules'][number]['provenance'],
  ) => {
    if (
      provenance.documentId &&
      provenance.pages &&
      provenance.pages.length > 0
    ) {
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
        testId: 'gfa-cap',
      },
      {
        key: 'floorsMax',
        label: t('wizard.results.metrics.floorsMax'),
        value: numberFormatter.format(result.metrics.floorsMax),
        testId: 'floors-max',
      },
      {
        key: 'footprintM2',
        label: t('wizard.results.metrics.footprint'),
        value: numberFormatter.format(result.metrics.footprintM2),
        testId: 'footprint',
      },
      {
        key: 'nsaEstM2',
        label: t('wizard.results.metrics.nsa'),
        value: numberFormatter.format(result.metrics.nsaEstM2),
        testId: 'nsa-est',
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

  const assetMixView = useMemo(() => {
    if (!capturedAssetMix.length) {
      return null
    }

    const formatRow = (plan: StoredAssetOptimization) => {
      const parts: string[] = [`${numberFormatter.format(plan.allocationPct)}%`]
      if (plan.allocatedGfaSqm != null) {
        parts.push(`${numberFormatter.format(Math.round(plan.allocatedGfaSqm))} sqm`)
      }
      if (plan.niaEfficiency != null) {
        parts.push(`${oneDecimalFormatter.format(plan.niaEfficiency * 100)}% NIA`)
      }
      if (plan.targetFloorHeightM != null) {
        parts.push(`${oneDecimalFormatter.format(plan.targetFloorHeightM)} m floors`)
      }
      if (plan.parkingRatioPer1000Sqm != null) {
        parts.push(
          `${oneDecimalFormatter.format(plan.parkingRatioPer1000Sqm)} lots / 1000 sqm`,
        )
      }
      if (plan.estimatedRevenueSgd != null && plan.estimatedRevenueSgd > 0) {
        parts.push(
          `Rev ≈ $${oneDecimalFormatter.format(plan.estimatedRevenueSgd / 1_000_000)}M`,
        )
      }
      if (plan.estimatedCapexSgd != null && plan.estimatedCapexSgd > 0) {
        parts.push(
          `CAPEX ≈ $${oneDecimalFormatter.format(plan.estimatedCapexSgd / 1_000_000)}M`,
        )
      }
      if (plan.riskLevel) {
        const risk = `${plan.riskLevel.charAt(0).toUpperCase()}${plan.riskLevel.slice(1)}`
        parts.push(
          `${risk} risk${
            plan.absorptionMonths ? ` · ~${numberFormatter.format(plan.absorptionMonths)}m absorption` : ''
          }`,
        )
      }
      return parts.join(' • ')
    }

    return (
      <section className="feasibility-asset-mix" data-testid="asset-mix">
        <h3>Captured asset mix</h3>
        <dl>
          {capturedAssetMix.map((plan) => (
            <div key={plan.assetType} className="feasibility-asset-mix__item">
              <dt>{plan.assetType}</dt>
              <dd>{formatRow(plan)}</dd>
              {plan.notes && plan.notes.length > 0 && (
                <p className="feasibility-asset-mix__note">{plan.notes[0]}</p>
              )}
            </div>
          ))}
        </dl>
        {capturedFinancialSummary ? (
          <div className="feasibility-asset-mix__summary">
            <h4>Financial snapshot</h4>
            <ul>
              <li>
                Total revenue:{' '}
                {capturedFinancialSummary.totalEstimatedRevenueSgd != null
                  ? `$${oneDecimalFormatter.format(
                      capturedFinancialSummary.totalEstimatedRevenueSgd / 1_000_000,
                    )}M`
                  : '—'}
              </li>
              <li>
                Total capex:{' '}
                {capturedFinancialSummary.totalEstimatedCapexSgd != null
                  ? `$${oneDecimalFormatter.format(
                      capturedFinancialSummary.totalEstimatedCapexSgd / 1_000_000,
                    )}M`
                  : '—'}
              </li>
              <li>
                Dominant risk:{' '}
                {capturedFinancialSummary.dominantRiskProfile ?? '—'}
              </li>
            </ul>
            {capturedFinancialSummary.notes.length > 0 && (
              <p className="feasibility-asset-mix__note">
                {capturedFinancialSummary.notes[0]}
              </p>
            )}
          </div>
        ) : null}
      </section>
    )
  }, [capturedAssetMix, capturedFinancialSummary, numberFormatter, oneDecimalFormatter])

  const advisoryView = useMemo(() => {
    const hints = result?.advisoryHints ?? []
    if (hints.length === 0) {
      return null
    }
    return (
      <section className="feasibility-advisory" data-testid="advisory-hints">
        <h3>{t('wizard.results.advisory.title')}</h3>
        <ul>
          {hints.map((hint, index) => (
            <li key={`${hint}-${index}`}>{hint}</li>
          ))}
        </ul>
      </section>
    )
  }, [result, t])

  const headerActions = (
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
        <span
          className="feasibility-wizard__copy-status"
          role="status"
          style={{ color: copyStatusColor }}
        >
          {t('wizard.form.copySuccess')}
        </span>
      )}
      {copyState === 'error' && (
        <span
          className="feasibility-wizard__copy-status"
          role="status"
          style={{ color: copyStatusColor }}
        >
          {t('wizard.form.copyError')}
        </span>
      )}
    </div>
  )

  const wizardBody = (
    <div className="feasibility-wizard" data-testid="feasibility-wizard">
        <div className="feasibility-wizard__layout">
          <section className="feasibility-wizard__controls">
            <form
              className="feasibility-form"
              onSubmit={handleSubmit}
              noValidate
            >
              <label
                className="feasibility-form__label"
                htmlFor="address-input"
              >
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
                  data-testid="address-input"
                />
                {addressError && (
                  <p className="feasibility-form__error">{addressError}</p>
                )}
              </div>
              <div className="feasibility-form__actions">
                <button
                  type="submit"
                  className="feasibility-form__submit"
                  data-testid="compute-button"
                >
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
                    data-testid="assumption-floor"
                  />
                  <p className="feasibility-assumptions__hint">
                    {t('wizard.assumptions.fields.typFloorToFloor.hint', {
                      value: decimalFormatter.format(
                        DEFAULT_ASSUMPTIONS.typFloorToFloorM,
                      ),
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
                      value: decimalFormatter.format(
                        DEFAULT_ASSUMPTIONS.efficiencyRatio,
                      ),
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

            <section className="feasibility-pack">
              <h2>{t('wizard.pack.title')}</h2>
              <p>{t('wizard.pack.subtitle')}</p>
              <form className="feasibility-pack__form" onSubmit={handlePackSubmit}>
                <label className="feasibility-pack__field">
                  <span>{t('wizard.pack.propertyLabel')}</span>
                  <input
                    type="text"
                    value={packPropertyId}
                    onChange={(event) => setPackPropertyId(event.target.value)}
                    placeholder={t('wizard.pack.propertyPlaceholder')}
                    data-testid="feasibility-pack-property"
                  />
                  <small>{t('wizard.pack.propertyHelper')}</small>
                </label>
                <label className="feasibility-pack__field">
                  <span>{t('wizard.pack.typeLabel')}</span>
                  <select
                    value={packType}
                    onChange={(event) =>
                      setPackType(event.target.value as ProfessionalPackType)
                    }
                    data-testid="feasibility-pack-type"
                  >
                    {PACK_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {t(option.labelKey)}
                      </option>
                    ))}
                  </select>
                  <small>{t(selectedPackOption.descriptionKey)}</small>
                </label>
                <button
                  type="submit"
                  className="feasibility-pack__submit"
                  disabled={packLoading}
                  data-testid="feasibility-pack-submit"
                >
                  {packLoading
                    ? t('wizard.pack.generateLoading')
                    : t('wizard.pack.generate')}
                </button>
              </form>
              {packError && (
                <p className="feasibility-pack__error" role="alert">
                  {t('wizard.pack.error', { message: packError })}
                </p>
              )}
              {packSummary && (
                <div className="feasibility-pack__result">
                  <p>
                    {t('wizard.pack.generatedAt', {
                      timestamp: new Date(packSummary.generatedAt).toLocaleString(
                        i18n.language || 'en',
                      ),
                    })}
                  </p>
                  <p>
                    {t('wizard.pack.size', {
                      size: formatFileSize(packSummary.sizeBytes, i18n.language || 'en'),
                    })}
                  </p>
                  {packSummary.downloadUrl ? (
                    <a
                      href={packSummary.downloadUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="feasibility-pack__download"
                    >
                      {t('wizard.pack.downloadCta', {
                        filename: packSummary.filename,
                      })}
                    </a>
                  ) : (
                    <p>{t('wizard.pack.noDownload')}</p>
                  )}
                </div>
              )}
            </section>
          </section>

          <section
            className="feasibility-results"
            aria-live="polite"
            aria-busy={status === 'loading'}
          >
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

            {(status === 'success' ||
              status === 'partial' ||
              status === 'empty') &&
              result && (
                <div className="feasibility-results__content">
                  <header className="feasibility-results__header">
                    <div>
                      <span className="feasibility-results__label">
                        {t('wizard.results.zone')}
                      </span>
                      <span
                        className="feasibility-results__value"
                        data-testid="zone-code"
                      >
                        {result.zoneCode ?? t('wizard.results.zoneUnknown')}
                      </span>
                    </div>
                    <div>
                      <span className="feasibility-results__label">
                        {t('wizard.results.overlays')}
                      </span>
                      <div
                        className="feasibility-results__overlays"
                        data-testid="overlay-badges"
                      >
                        {result.overlays.length === 0 && (
                          <span className="feasibility-results__badge">
                            {t('wizard.results.none')}
                          </span>
                        )}
                        {result.overlays.map((overlay) => (
                          <span
                            key={overlay}
                            className="feasibility-results__badge"
                          >
                            {overlay}
                          </span>
                        ))}
                      </div>
                    </div>
                  </header>

                  {metricsView}
                  {assetMixView}

                  {advisoryView}

                  {status === 'empty' && (
                    <p className="feasibility-results__empty">
                      {t('wizard.states.empty')}
                    </p>
                  )}

                  {status === 'partial' && result.zoneCode && (
                    <p className="feasibility-results__partial">
                      {t('wizard.states.partial')}
                    </p>
                  )}

                  {result.rules.length > 0 && (
                    <section
                      className="feasibility-citations"
                      data-testid="citations"
                    >
                      <h3>{t('wizard.citations.title')}</h3>
                      <ul>
                        {result.rules.map((rule) => (
                          <li key={rule.id} className="feasibility-citation">
                            <div className="feasibility-citation__meta">
                              <span className="feasibility-citation__authority">
                                {rule.authority}
                              </span>
                              <span className="feasibility-citation__clause">
                                {rule.provenance.clauseRef ??
                                  t('wizard.citations.unknownClause')}
                              </span>
                            </div>
                            <p className="feasibility-citation__parameter">
                              {`${rule.parameterKey} ${rule.operator} ${
                                rule.value
                              }${rule.unit ? ` ${rule.unit}` : ''}`}
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

  if (!withLayout) {
    return (
      <div className="feasibility-wizard__container">
        {headerActions}
        {wizardBody}
      </div>
    )
  }

  return (
    <AppLayout
      title={t('wizard.title')}
      subtitle={t('wizard.description')}
      actions={headerActions}
    >
      {wizardBody}
    </AppLayout>
  )
}

export default FeasibilityWizard
