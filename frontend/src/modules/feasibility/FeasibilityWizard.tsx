import type { ChangeEvent, FormEvent } from 'react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Snackbar, Alert } from '@mui/material'

import { AppLayout } from '../../App'
import {
  generateProfessionalPack,
  type ProfessionalPackType,
} from '../../api/agents'
import { useTranslation } from '../../i18n'
import { useRouterLocation } from '../../router'

import {
  AddressForm,
  AssumptionsPanel,
  FinancialSettingsPanel,
  PackGenerationPanel,
  ResultsPanel,
  FeasibilityLayout,
  SmartIntelligenceField,
  PackGrid,
  ScenarioHistorySidebar,
  GenerativeDesignPanel,
  AIAssistantSidebar,
  ImmersiveMap,
  ScenarioSelector,
  type HistoryItem,
} from './components'

// Import MUI Dialog components for the "Flipbook" preview
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
} from '@mui/material'
import {
  Description as PdfIcon,
  Download as DownloadIcon,
  History as HistoryIcon,
  SmartToy,
  Radar,
} from '@mui/icons-material'
import {
  useAssumptions,
  useFeasibilityCompute,
  usePackGeneration,
  useFinancials,
  useAIAssistant,
} from './hooks'
import type { PendingPayload, GenerativeStrategy } from './types'
import {
  createDecimalFormatter,
  createNumberFormatter,
} from './utils/formatters'
import '../../styles/feasibility.css'

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
  const [copyState, setCopyState] = useState<'idle' | 'copied' | 'error'>(
    'idle',
  )
  const copyResetRef = useRef<number | null>(null)

  // History State
  const [historyOpen, setHistoryOpen] = useState(false)
  const [history, setHistory] = useState<HistoryItem[]>([])

  // AI Assistant State
  const [aiSidebarOpen, setAiSidebarOpen] = useState(false)
  const { messages, isTyping, sendMessage } = useAIAssistant()

  // Generative State
  const [generativeStrategy, setGenerativeStrategy] =
    useState<GenerativeStrategy | null>(null)

  // Custom hooks
  const {
    assumptionInputs,
    assumptionErrors,
    appliedAssumptions,
    handleAssumptionChange,
    handleResetAssumptions,
  } = useAssumptions()

  // Financial hooks
  const {
    financialInputs,
    financialErrors,
    appliedFinancials,
    handleFinancialChange,
  } = useFinancials()

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

  // State for Flipbook Preview Modal
  const [isPreviewOpen, setIsPreviewOpen] = useState(false)
  const [packGenerating, setPackGenerating] = useState(false)

  const handleGeneratePack = async () => {
    setPackGenerating(true)
    // Simulate generation delay
    await new Promise((resolve) => setTimeout(resolve, 1500))
    setPackGenerating(false)
    setIsPreviewOpen(true)
  }

  // Sync assumptions with payload
  useEffect(() => {
    updatePayloadAssumptions(
      appliedAssumptions.typFloorToFloorM,
      appliedAssumptions.efficiencyRatio,
    )
  }, [appliedAssumptions, updatePayloadAssumptions])

  // Optimization Logic: Update assumptions based on Generative Strategy
  useEffect(() => {
    if (!generativeStrategy) return

    const syntheticEvent = (val: string) =>
      ({ target: { value: val } }) as ChangeEvent<HTMLInputElement>

    switch (generativeStrategy) {
      case 'max_density':
        handleAssumptionChange('efficiencyRatio')(syntheticEvent('0.92'))
        handleAssumptionChange('typFloorToFloorM')(syntheticEvent('3.2'))
        break
      case 'balanced':
        handleAssumptionChange('efficiencyRatio')(syntheticEvent('0.85'))
        handleAssumptionChange('typFloorToFloorM')(syntheticEvent('3.5'))
        break
      case 'iconic':
        handleAssumptionChange('efficiencyRatio')(syntheticEvent('0.75'))
        handleAssumptionChange('typFloorToFloorM')(syntheticEvent('4.0')) // Higher ceilings
        break
      case 'green_focus':
        handleAssumptionChange('efficiencyRatio')(syntheticEvent('0.70'))
        // Maybe structureType = mass_timber if we could
        break
    }
    // Set to null to avoid infinite loops if user manually changes back,
    // or keep it selected to show active mode?
    // For now, let's keep it but we need to be careful not to loop.
    // Actually, improved UX: just one-time apply.
    setGenerativeStrategy(null)

    // Trigger submit to refresh results
    // We can't easily trigger handleSubmit (event) from here.
    // But updating handleAssumptionChange updates 'appliedAssumptions',
    // which effectively updates the form state.
    // The user might still need to click 'Run Analysis' or we can auto-run.
    // Let's rely on the user or the "Auto-Compute" nature if we had it.
    // For now, these simulation changes are enough.
  }, [generativeStrategy, handleAssumptionChange])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (copyResetRef.current !== null) {
        clearTimeout(copyResetRef.current)
      }
    }
  }, [])

  // Update handleSubmit to save history on SUCCESS
  // We need to watch for result changes to trigger save, or do it in the effect/callback
  // Ideally, useFeasibilityCompute would return a "lastSuccessTimestamp" or similar.
  // For now, let's wrap the setPayload and detect success in an effect.

  useEffect(() => {
    if (status === 'success' && result && payload) {
      setHistory((prev) => {
        // Prevent duplicate saves for same payload
        const last = prev[0]
        if (last && JSON.stringify(last.payload) === JSON.stringify(payload)) {
          return prev
        }
        const newItem: HistoryItem = {
          id: Date.now().toString(),
          timestamp: new Date(),
          payload: payload,
          result: result,
        }
        return [newItem, ...prev]
      })
    }
  }, [status, result, payload])

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
        financials: appliedFinancials,
      })
      const trimmed = addressInput.trim()
      const siteArea = parseFloat(siteAreaInput)
      if (!trimmed) {
        setAddressError(t('wizard.form.errors.addressRequired'))
        setPayload(null)
        return
      }

      if (isNaN(siteArea) || siteArea <= 0) {
        setAddressError(
          t('wizard.form.errors.invalidSiteArea') || 'Invalid site area',
        )
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
        structureType: appliedAssumptions.structureType,
        mepLoadWpsm: appliedAssumptions.mepLoadWpsm,
        capRatePercent: appliedFinancials.capRatePercent,
        interestRatePercent: appliedFinancials.interestRatePercent,
        targetMarginPercent: appliedFinancials.targetMarginPercent,
      }
      console.log(
        'FeasibilityWizard: handleSubmit setting payload:',
        newPayload,
      )
      setPayload(newPayload)
    },
    [
      addressInput,
      siteAreaInput,
      landUseInput,
      appliedAssumptions,
      appliedFinancials,
      setPayload,
      t,
    ],
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
      structureType: payload.structureType,
      mepLoadWpsm: payload.mepLoadWpsm,
      capRatePercent: payload.capRatePercent,
      interestRatePercent: payload.interestRatePercent,
      targetMarginPercent: payload.targetMarginPercent,
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

  const handleRestore = useCallback(
    (item: HistoryItem) => {
      // 1. Restore Addresses
      setAddressInput(item.payload.address)
      setSiteAreaInput(item.payload.siteAreaSqm.toString())
      setLandUseInput(item.payload.landUse)

      // 2. Restore Assumptions (via hook methods if exposed, or just set inputs)
      // Since useAssumptions controls its own state, we need to manually reset its internal state
      // or just force the payload.
      // Ideally, the hooks should expose setters, but for now we set the inputs which drives the applied state.
      const syntheticEvent = (val: string) =>
        ({ target: { value: val } }) as ChangeEvent<HTMLInputElement>
      handleAssumptionChange('typFloorToFloorM')(
        syntheticEvent(item.payload.typFloorToFloorM.toString()),
      )
      handleAssumptionChange('efficiencyRatio')(
        syntheticEvent(item.payload.efficiencyRatio.toString()),
      )

      // Engineering
      if (item.payload.structureType) {
        handleAssumptionChange('structureType')(
          syntheticEvent(item.payload.structureType),
        )
      }
      if (item.payload.mepLoadWpsm) {
        handleAssumptionChange('mepLoadWpsm')(
          syntheticEvent(item.payload.mepLoadWpsm.toString()),
        )
      }

      // Financials
      if (item.payload.capRatePercent) {
        handleFinancialChange('capRatePercent')(
          syntheticEvent(item.payload.capRatePercent.toString()),
        )
      }
      if (item.payload.interestRatePercent) {
        handleFinancialChange('interestRatePercent')(
          syntheticEvent(item.payload.interestRatePercent.toString()),
        )
      }
      if (item.payload.targetMarginPercent) {
        handleFinancialChange('targetMarginPercent')(
          syntheticEvent(item.payload.targetMarginPercent.toString()),
        )
      }

      // 3. Set Payload (triggers re-compute effectively, or just restore result if we want)
      // If we want to view the cached result immediately:
      // setResult(item.result) // We can't set result directly as useFeasibilityCompute owns it.
      // So we just set payload to trigger re-run (or hit cache).
      setPayload(item.payload)
      setHistoryOpen(false)
    },
    [handleAssumptionChange, handleFinancialChange, setPayload],
  )

  // Render
  const headerActions = (
    <div className="feasibility-wizard__toolbar">
      <button
        type="button"
        onClick={() => setAiSidebarOpen(true)}
        className="feasibility-wizard__copy"
        style={{
          marginRight: '8px',
          display: 'inline-flex',
          alignItems: 'center',
          gap: '4px',
        }}
        title="AI Planner"
      >
        <SmartToy fontSize="small" /> AI Planner
      </button>

      <button
        type="button"
        onClick={() => setHistoryOpen(true)}
        className="feasibility-wizard__copy"
        style={{ marginRight: '8px' }} // Add some spacing
        title="View History"
      >
        <HistoryIcon fontSize="small" style={{ marginRight: '4px' }} /> History
      </button>

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
          className="feasibility-wizard__copy-status feasibility-wizard__copy-status--success"
          role="status"
        >
          {t('wizard.form.copySuccess')}
        </span>
      )}
      {copyState === 'error' && (
        <span
          className="feasibility-wizard__copy-status feasibility-wizard__copy-status--error"
          role="status"
        >
          {t('wizard.form.copyError')}
        </span>
      )}
    </div>
  )

  const wizardBody = (
    <div className="feasibility-wizard" data-testid="feasibility-wizard">
      <div className="feasibility-wizard__layout">
        <section
          className="feasibility-wizard__controls-transparent"
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '32px',
            color: 'rgba(255,255,255,0.9)',
          }}
        >
          <AddressForm
            addressInput={addressInput}
            addressError={addressError}
            status={status}
            onAddressChange={handleAddressChange}
            onSubmit={handleSubmit}
            t={t}
            siteAreaInput={siteAreaInput}
            onSiteAreaChange={handleSiteAreaChange}
            hideAddress={true}
            hideSubmit={true}
          />

          <AssumptionsPanel
            assumptionInputs={assumptionInputs}
            assumptionErrors={assumptionErrors}
            decimalFormatter={decimalFormatter}
            onAssumptionChange={handleAssumptionChange}
            onResetAssumptions={handleResetAssumptions}
            landUseInput={landUseInput}
            onLandUseChange={handleLandUseChange}
            t={t}
          />

          {/* New Financial Settings Panel */}
          <FinancialSettingsPanel
            financialInputs={financialInputs}
            financialErrors={financialErrors}
            onFinancialChange={handleFinancialChange}
          />

          <GenerativeDesignPanel
            selectedStrategy={generativeStrategy}
            onSelectStrategy={setGenerativeStrategy}
            loading={status === 'loading'}
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
          errorMessage={null} // Error handled by Toast
          capturedAssetMix={capturedAssetMix}
          capturedFinancialSummary={capturedFinancialSummary}
          numberFormatter={numberFormatter}
          oneDecimalFormatter={oneDecimalFormatter}
          t={t}
        />
      </div>

      <Snackbar
        open={status === 'error'}
        autoHideDuration={6000}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert severity="error" variant="filled" sx={{ width: '100%' }}>
          {errorMessage || t('wizard.errors.generic')}
        </Alert>
      </Snackbar>

      <div className="sr-only" aria-live="polite">
        {liveAnnouncement}
      </div>

      {/* Scenario History Sidebar */}
      <ScenarioHistorySidebar
        open={historyOpen}
        onClose={() => setHistoryOpen(false)}
        history={history}
        onRestore={handleRestore}
      />

      <AIAssistantSidebar
        open={aiSidebarOpen}
        onClose={() => setAiSidebarOpen(false)}
        messages={messages}
        onSendMessage={sendMessage}
        isTyping={isTyping}
      />

      {/* Flipbook Dialog ... */}
      {/* Flipbook Preview Modal */}
      <Dialog
        open={isPreviewOpen}
        onClose={() => setIsPreviewOpen(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: { borderRadius: 'var(--ob-radius-lg)', overflow: 'hidden' },
        }}
      >
        <DialogTitle
          sx={{
            borderBottom: '1px solid var(--ob-color-border-light)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <span>
            Pack Preview: {packType.charAt(0).toUpperCase() + packType.slice(1)}
          </span>
          <Typography variant="caption" sx={{ color: 'text.secondary' }}>
            LIVE GENERATION
          </Typography>
        </DialogTitle>
        <DialogContent
          sx={{
            minHeight: '400px',
            background: 'var(--ob-color-bg-surface-secondary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 0,
          }}
        >
          <div
            style={{
              width: '300px',
              height: '420px',
              background: 'white',
              boxShadow: '0 20px 40px rgba(0,0,0,0.2)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: '4px',
              position: 'relative',
              transition: 'transform 0.3s',
            }}
          >
            <div
              style={{
                width: '100%',
                height: '180px',
                background: 'var(--ob-color-bg-surface-secondary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: 'auto',
              }}
            >
              {/* Placeholder for Cover Image */}
              <span style={{ fontSize: '3rem' }}>🏢</span>
            </div>
            <div style={{ padding: '2rem', textAlign: 'center' }}>
              <Typography variant="h6" gutterBottom>
                {addressInput || 'Site Address'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Optimal Build Professional Pack
              </Typography>
              <div
                style={{
                  marginTop: '1rem',
                  height: '4px',
                  width: '40px',
                  background: 'var(--ob-color-brand-primary)',
                  marginInline: 'auto',
                }}
              />
            </div>
            <div
              style={{
                marginTop: 'auto',
                padding: '1rem',
                width: '100%',
                borderTop: '1px solid var(--ob-color-border-light)',
                display: 'flex',
                justifyContent: 'space-between',
              }}
            >
              <span
                style={{
                  fontSize: '0.7rem',
                  color: 'var(--ob-color-text-muted)',
                }}
              >
                GENERATED: {new Date().toLocaleDateString()}
              </span>
              <span
                style={{
                  fontSize: '0.7rem',
                  color: 'var(--ob-color-text-muted)',
                }}
              >
                PAGE 1/12
              </span>
            </div>
          </div>
        </DialogContent>
        <DialogActions
          sx={{
            padding: '1rem',
            borderTop: '1px solid var(--ob-color-border-light)',
          }}
        >
          <Button
            onClick={() => setIsPreviewOpen(false)}
            sx={{ color: 'text.secondary' }}
          >
            Close
          </Button>
          <Button
            variant="contained"
            startIcon={<DownloadIcon />}
            onClick={() =>
              generatePackFn?.(
                propertyIdFromQuery || 'demo',
                packType as ProfessionalPackType,
              )
            }
          >
            Download PDF
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  )

  // Render Maps
  const renderMap = () => (
    <div style={{ height: '100%', width: '100%' }}>
      <ImmersiveMap
        latitude={1.285}
        longitude={103.854}
        onCoordinatesChange={(lat, lon) => console.log('Map coords:', lat, lon)}
        showCentralCTA={status === 'idle' && !addressInput}
        onAddressSearch={(address) => {
          setAddressInput(address)
          // Auto-trigger search when user enters address from central CTA
          if (address.trim()) {
            setAddressError(null)
          }
        }}
      />
    </div>
  )

  // Note: PropertyLocationMap is imported at the top of the file in the full implementation
  // We need to ensure we import it. Since this is a partial replace, I'll add the layout usage.

  if (!withLayout) {
    return (
      <div className="feasibility-wizard__container">
        {headerActions}
        {wizardBody}
      </div>
    )
  }

  // To properly implement the split screen, we need to completely restructure the return.
  // I will return the new FeasibilityLayout structure.

  return (
    <AppLayout
      title={t('wizard.title')}
      subtitle={t('wizard.description')}
      actions={headerActions}
    >
      <FeasibilityLayout
        renderMap={renderMap}
        scorecardProps={{
          siteArea: parseFloat(siteAreaInput) || 0,
          efficiencyRatio: appliedAssumptions.efficiencyRatio,
          floorToFloor: appliedAssumptions.typFloorToFloorM,
          plotRatio: 2.8, // Could be made dynamic based on zoning
          visible: !!siteAreaInput && parseFloat(siteAreaInput) > 0,
        }}
        renderFooter={() => (
          <div
            className="feasibility-actions"
            style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}
          >
            <button
              onClick={() => {
                const syntheticEvent = {
                  preventDefault: () => {},
                } as FormEvent<HTMLFormElement>
                handleSubmit(syntheticEvent)
              }}
              disabled={status === 'loading'}
              style={{
                background:
                  'linear-gradient(135deg, var(--ob-color-brand-primary), var(--ob-color-brand-primary-emphasis))',
                border: 'none',
                borderRadius: 'var(--ob-radius-full)',
                padding: '16px 32px',
                color: 'white',
                fontWeight: 700,
                fontSize: '1.1rem',
                letterSpacing: '0.02em',
                cursor: status === 'loading' ? 'wait' : 'pointer',
                boxShadow: '0 4px 14px 0 rgba(0,118,255,0.39)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '12px',
                transition: 'transform 0.2s, box-shadow 0.2s',
                width: '100%',
                position: 'relative',
                overflow: 'hidden',
              }}
              onMouseEnter={(e) =>
                (e.currentTarget.style.transform = 'translateY(-2px)')
              }
              onMouseLeave={(e) =>
                (e.currentTarget.style.transform = 'translateY(0)')
              }
            >
              {status === 'loading' ? (
                <>
                  <span
                    className="radar-spinner"
                    style={{
                      width: '20px',
                      height: '20px',
                      border: '2px solid white',
                      borderTopColor: 'transparent',
                      borderRadius: '50%',
                      animation: 'spin 1s linear infinite',
                    }}
                  />
                  <span>Scanning Site...</span>
                </>
              ) : (
                <>
                  <Radar sx={{ animation: 'pulse 2s infinite' }} />
                  <span>RUN SIMULATION</span>
                </>
              )}

              {/* Button Glow Effect */}
              <div
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  background:
                    'linear-gradient(to right, transparent, rgba(255,255,255,0.2), transparent)',
                  transform: 'skewX(-20deg) translateX(-150%)',
                  animation: 'shimmer 3s infinite',
                }}
              />
              <style>{`
                        @keyframes shimmer { 0% { transform: translateX(-150%) skewX(-20deg); } 20% { transform: translateX(150%) skewX(-20deg); } 100% { transform: translateX(150%); } }
                        @keyframes pulse { 0% { opacity: 0.6; transform: scale(0.9); } 50% { opacity: 1; transform: scale(1.1); } 100% { opacity: 0.6; transform: scale(0.9); } }
                     `}</style>
            </button>
          </div>
        )}
      >
        <div className="feasibility-wizard__sidebar-content">
          {/* Section 0: Smart Intelligence Field (Merged Address/Area/Zoning) */}
          <div className="ob-section-gap">
            <SmartIntelligenceField
              value={addressInput}
              siteArea={siteAreaInput ? Number(siteAreaInput) : undefined}
              zoning={landUseInput}
              onChange={handleAddressChange}
              onSubmit={(e: FormEvent<HTMLFormElement>) => {
                e.preventDefault()
                handleSubmit(e)
              }}
              loading={status === 'loading'}
              error={addressError}
              onSuggestionSelect={(suggestion: {
                address: string
                siteArea: number
                zoning: string
              }) => {
                setAddressInput(suggestion.address)
                setSiteAreaInput(suggestion.siteArea.toString())
                setLandUseInput(suggestion.zoning)
                setAddressError(null)
              }}
            />
          </div>
          {/* Section 1: Site Details - Depth 1 Glass Card */}
          <div className="feasibility-section ob-card-module ob-section-gap">
            <h3
              className="ob-page-header__subtitle"
              style={{ margin: 0, marginBottom: 'var(--ob-space-200)' }}
            >
              {t('wizard.steps.siteDetails')}
            </h3>
            <div className="feasibility-form__field">
              <label className="feasibility-form__label">
                {t('wizard.form.siteArea')}
              </label>
              <input
                type="number"
                value={siteAreaInput}
                onChange={handleSiteAreaChange}
                placeholder="e.g. 1000"
                data-testid="site-area-input"
              />
            </div>
            <div
              className="feasibility-form__field"
              style={{ marginTop: 'var(--ob-space-200)' }}
            >
              <label
                className="feasibility-form__label"
                style={{
                  marginBottom: 'var(--ob-space-150)',
                  display: 'block',
                }}
              >
                {t('wizard.form.landUse')}
              </label>
              <ScenarioSelector
                value={landUseInput}
                onChange={(val) => setLandUseInput(val)}
              />
            </div>
          </div>

          {/* Section 2: Assumptions - Depth 1 Glass Card */}
          <div className="feasibility-section ob-card-module ob-section-gap">
            <AssumptionsPanel
              assumptionInputs={assumptionInputs}
              assumptionErrors={assumptionErrors}
              decimalFormatter={decimalFormatter}
              onAssumptionChange={handleAssumptionChange}
              onResetAssumptions={handleResetAssumptions}
              t={t}
            />
          </div>

          {/* Section 2b: Financial Settings - Depth 1 Glass Card */}
          <div className="feasibility-section ob-card-module ob-section-gap">
            <FinancialSettingsPanel
              financialInputs={financialInputs}
              financialErrors={financialErrors}
              onFinancialChange={handleFinancialChange}
            />
          </div>

          {/* Section 3: Computing Action - MOVED TO STICKY FOOTER */}

          {/* Section 4: Results (Dynamic) - Depth 1 Glass Card */}
          {result && (
            <div className="feasibility-section ob-card-module ob-section-gap">
              <ResultsPanel
                status={status}
                result={result}
                errorMessage={null}
                capturedAssetMix={capturedAssetMix}
                capturedFinancialSummary={capturedFinancialSummary}
                numberFormatter={numberFormatter}
                oneDecimalFormatter={oneDecimalFormatter}
                t={t}
              />
            </div>
          )}

          {/* Section 5: Packs - Depth 1 Glass Card */}
          {result && (
            <div className="feasibility-section ob-card-module ob-section-gap">
              <PackGrid
                value={packType}
                onChange={setPackType}
                options={[
                  {
                    value: 'universal',
                    label: 'Universal Pack',
                    description: 'Site plan & zoning',
                  },
                  {
                    value: 'investment',
                    label: 'Investment Memo',
                    description: 'Financial model & ROI',
                  },
                  {
                    value: 'sales',
                    label: 'Sales Brochure',
                    description: 'Buyer-ready visuals',
                  },
                  {
                    value: 'lease',
                    label: 'Leasing Deck',
                    description: 'Floor efficiency & tenant mix',
                  },
                ]}
              />
              <div
                style={{
                  marginTop: '1rem',
                  display: 'flex',
                  justifyContent: 'flex-end',
                }}
              >
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleGeneratePack}
                  disabled={packGenerating}
                  startIcon={
                    packGenerating ? (
                      <span
                        className="scenario-fab__spinner"
                        style={{
                          width: 16,
                          height: 16,
                          border: '2px solid white',
                          borderTopColor: 'transparent',
                        }}
                      />
                    ) : (
                      <PdfIcon />
                    )
                  }
                  sx={{
                    fontFamily: 'var(--ob-font-family-sans)',
                    textTransform: 'none',
                    fontWeight: 600,
                    boxShadow: 'var(--ob-shadow-md)',
                    background: 'var(--ob-color-brand-primary)',
                    '&:hover': { background: 'var(--ob-color-brand-dark)' },
                  }}
                >
                  {packGenerating
                    ? 'Generating Preview...'
                    : 'Preview & Generate Pack'}
                </Button>
              </div>
            </div>
          )}

          {/* Flipbook Preview Modal */}
          <Dialog
            open={isPreviewOpen}
            onClose={() => setIsPreviewOpen(false)}
            maxWidth="md"
            fullWidth
            PaperProps={{
              sx: { borderRadius: 'var(--ob-radius-lg)', overflow: 'hidden' },
            }}
          >
            <DialogTitle
              sx={{
                borderBottom: '1px solid var(--ob-color-border-light)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <span>
                Pack Preview:{' '}
                {packType.charAt(0).toUpperCase() + packType.slice(1)}
              </span>
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                LIVE GENERATION
              </Typography>
            </DialogTitle>
            <DialogContent
              sx={{
                minHeight: '400px',
                background: 'var(--ob-color-bg-surface-secondary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: 0,
              }}
            >
              <div
                style={{
                  width: '300px',
                  height: '420px',
                  background: 'white',
                  boxShadow: '0 20px 40px rgba(0,0,0,0.2)',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  borderRadius: '4px',
                  position: 'relative',
                  transition: 'transform 0.3s',
                }}
              >
                <div
                  style={{
                    width: '100%',
                    height: '180px',
                    background: 'var(--ob-color-bg-surface-secondary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    marginBottom: 'auto',
                  }}
                >
                  {/* Placeholder for Cover Image */}
                  <span style={{ fontSize: '3rem' }}>🏢</span>
                </div>
                <div style={{ padding: '2rem', textAlign: 'center' }}>
                  <Typography variant="h6" gutterBottom>
                    {addressInput || 'Site Address'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Optimal Build Professional Pack
                  </Typography>
                  <div
                    style={{
                      marginTop: '1rem',
                      height: '4px',
                      width: '40px',
                      background: 'var(--ob-color-brand-primary)',
                      marginInline: 'auto',
                    }}
                  />
                </div>
                <div
                  style={{
                    marginTop: 'auto',
                    padding: '1rem',
                    width: '100%',
                    borderTop: '1px solid var(--ob-color-border-light)',
                    display: 'flex',
                    justifyContent: 'space-between',
                  }}
                >
                  <span
                    style={{
                      fontSize: '0.7rem',
                      color: 'var(--ob-color-text-muted)',
                    }}
                  >
                    GENERATED: {new Date().toLocaleDateString()}
                  </span>
                  <span
                    style={{
                      fontSize: '0.7rem',
                      color: 'var(--ob-color-text-muted)',
                    }}
                  >
                    PAGE 1/12
                  </span>
                </div>
              </div>
            </DialogContent>
            <DialogActions
              sx={{
                padding: '1rem',
                borderTop: '1px solid var(--ob-color-border-light)',
              }}
            >
              <Button
                onClick={() => setIsPreviewOpen(false)}
                sx={{ color: 'text.secondary' }}
              >
                Close
              </Button>
              <Button
                variant="contained"
                startIcon={<DownloadIcon />}
                onClick={() =>
                  generatePackFn?.(
                    propertyIdFromQuery || 'demo',
                    packType as ProfessionalPackType,
                  )
                }
              >
                Download PDF
              </Button>
            </DialogActions>
          </Dialog>
        </div>
      </FeasibilityLayout>
    </AppLayout>
  )
}

export default FeasibilityWizard
