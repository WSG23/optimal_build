import type { ChangeEvent, FormEvent } from 'react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { AppLayout } from '../../App'
import { generateProfessionalPack, type ProfessionalPackType } from '../../api/agents'
import { useTranslation } from '../../i18n'
import { useRouterLocation } from '../../router'

import { AddressForm, AssumptionsPanel, PackGenerationPanel, ResultsPanel } from './components'
import { useAssumptions, useFeasibilityCompute, usePackGeneration } from './hooks'
import type { PendingPayload } from './types'
import { createDecimalFormatter, createNumberFormatter, readCssVar } from './utils/formatters'

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

  // Address state
  const [addressInput, setAddressInput] = useState('')
  const [addressError, setAddressError] = useState<string | null>(null)
  const [siteAreaInput, setSiteAreaInput] = useState('')
  const [landUseInput, setLandUseInput] = useState('Mixed Use')

  // Copy state
  const [copyState, setCopyState] = useState<'idle' | 'copied' | 'error'>('idle')
  const copyResetRef = useRef<number | null>(null)

  // Custom hooks
  const {
    assumptionInputs,
    assumptionErrors,
    appliedAssumptions,
    handleAssumptionChange,
    handleResetAssumptions,
  } = useAssumptions()

  const {
    result,
    status,
    errorMessage,
    liveAnnouncement,
    payload,
    setPayload,
    updatePayloadAssumptions,
  } = useFeasibilityCompute({ t })

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

  const {
    packPropertyId,
    packType,
    packSummary,
    packLoading,
    packError,
    capturedAssetMix,
    capturedFinancialSummary,
    handlePackSubmit,
    setPackPropertyId,
    setPackType,
    selectedPackOption,
  } = usePackGeneration({
    propertyIdFromQuery,
    generatePackFn,
    t,
  })

  // Formatters
  const numberFormatter = useMemo(
    () => createNumberFormatter(i18n.language),
    [i18n.language],
  )

  const oneDecimalFormatter = useMemo(
    () => createNumberFormatter(i18n.language, 1),
    [i18n.language],
  )

  const decimalFormatter = useMemo(
    () => createDecimalFormatter(i18n.language),
    [i18n.language],
  )

  const copyStatusColor = useMemo<string>(() => {
    if (copyState === 'copied') {
      return readCssVar('color-success-strong')
    }
    if (copyState === 'error') {
      return readCssVar('color-error-strong')
    }
    return readCssVar('color-brand-primary')
  }, [copyState])

  // Sync assumptions with payload
  useEffect(() => {
    updatePayloadAssumptions(
      appliedAssumptions.typFloorToFloorM,
      appliedAssumptions.efficiencyRatio,
    )
  }, [appliedAssumptions, updatePayloadAssumptions])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (copyResetRef.current !== null) {
        clearTimeout(copyResetRef.current)
      }
    }
  }, [])

  // Handlers
  const handleAddressChange = useCallback(
    (event: ChangeEvent<HTMLInputElement>) => {
      setAddressInput(event.target.value)
      setAddressError(null)
    },
    [],
  )

  const handleSiteAreaChange = useCallback(
    (event: ChangeEvent<HTMLInputElement>) => {
      setSiteAreaInput(event.target.value)
    },
    [],
  )

  const handleLandUseChange = useCallback(
    (event: ChangeEvent<HTMLSelectElement>) => {
      setLandUseInput(event.target.value)
    },
    [],
  )

  const handleSubmit = useCallback(
    (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault()
      console.log('FeasibilityWizard: handleSubmit called')
      console.log('FeasibilityWizard: Inputs -', {
        addressInput,
        siteAreaInput,
        landUseInput,
        assumptions: appliedAssumptions,
      })
      const trimmed = addressInput.trim()
      const siteArea = parseFloat(siteAreaInput)
      if (!trimmed) {
        setAddressError(t('wizard.form.errors.addressRequired'))
        setPayload(null)
        return
      }

      if (isNaN(siteArea) || siteArea <= 0) {
        setAddressError(t('wizard.form.errors.invalidSiteArea') || 'Invalid site area')
        return
      }

      setAddressError(null)
      const newPayload: PendingPayload = {
        name: `Project ${trimmed}`,
        address: trimmed,
        siteAreaSqm: siteArea,
        landUse: landUseInput,
        typFloorToFloorM: appliedAssumptions.typFloorToFloorM,
        efficiencyRatio: appliedAssumptions.efficiencyRatio,
      }
      console.log('FeasibilityWizard: handleSubmit setting payload:', newPayload)
      setPayload(newPayload)
    },
    [addressInput, siteAreaInput, landUseInput, appliedAssumptions, setPayload, t],
  )

  const handleCopyRequest = useCallback(() => {
    if (!payload) {
      return
    }
    if (copyResetRef.current !== null) {
      clearTimeout(copyResetRef.current)
    }
    const body: PendingPayload = {
      name: payload.name,
      address: payload.address,
      siteAreaSqm: payload.siteAreaSqm,
      landUse: payload.landUse,
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

  const handlePackPropertyIdChange = useCallback(
    (value: string) => {
      setPackPropertyId(value)
    },
    [setPackPropertyId],
  )

  const handlePackTypeChange = useCallback(
    (value: ProfessionalPackType) => {
      setPackType(value)
    },
    [setPackType],
  )

  // Render
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
          <AddressForm
            addressInput={addressInput}
            addressError={addressError}
            status={status}
            onAddressChange={handleAddressChange}
            onSubmit={handleSubmit}
            t={t}
            siteAreaInput={siteAreaInput}
            landUseInput={landUseInput}
            onSiteAreaChange={handleSiteAreaChange}
            onLandUseChange={handleLandUseChange}
          />

          <AssumptionsPanel
            assumptionInputs={assumptionInputs}
            assumptionErrors={assumptionErrors}
            decimalFormatter={decimalFormatter}
            onAssumptionChange={handleAssumptionChange}
            onResetAssumptions={handleResetAssumptions}
            t={t}
          />

          <PackGenerationPanel
            packPropertyId={packPropertyId}
            packType={packType}
            packSummary={packSummary}
            packLoading={packLoading}
            packError={packError}
            selectedPackOption={selectedPackOption}
            locale={i18n.language || 'en'}
            onPropertyIdChange={handlePackPropertyIdChange}
            onPackTypeChange={handlePackTypeChange}
            onSubmit={handlePackSubmit}
            t={t}
          />
        </section>

        <ResultsPanel
          status={status}
          result={result}
          errorMessage={errorMessage}
          capturedAssetMix={capturedAssetMix}
          capturedFinancialSummary={capturedFinancialSummary}
          numberFormatter={numberFormatter}
          oneDecimalFormatter={oneDecimalFormatter}
          t={t}
        />
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
