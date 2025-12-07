import type { ChangeEvent, FormEvent } from 'react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Snackbar, Alert } from '@mui/material'

import { AppLayout } from '../../App'
import { generateProfessionalPack, type ProfessionalPackType } from '../../api/agents'
import { useTranslation } from '../../i18n'
import { useRouterLocation } from '../../router'

import {
  AddressForm,
  AssumptionsPanel,
  FinancialSettingsPanel,
  PackGenerationPanel,
  ResultsPanel,
  FeasibilityLayout,
  SmartSearchBar,
  PackGrid,
  ScenarioFAB,
  ScenarioHistorySidebar,
  GenerativeDesignPanel,
  AIAssistantSidebar,
  type HistoryItem
} from './components'

// Import MUI Dialog components for the "Flipbook" preview
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography
} from '@mui/material'
import { Description as PdfIcon, Download as DownloadIcon, History as HistoryIcon, SmartToy } from '@mui/icons-material'
import { useAssumptions, useFeasibilityCompute, usePackGeneration, useFinancials, useAIAssistant } from './hooks'
import type { PendingPayload, GenerativeStrategy } from './types'
import { createDecimalFormatter, createNumberFormatter } from './utils/formatters'

import { PropertyLocationMap } from '@/app/pages/site-acquisition/components/map/PropertyLocationMap'

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

  // History State
  const [historyOpen, setHistoryOpen] = useState(false)
  const [history, setHistory] = useState<HistoryItem[]>([])

  // AI Assistant State
  const [aiSidebarOpen, setAiSidebarOpen] = useState(false)
  const { messages, isTyping, sendMessage } = useAIAssistant()

  // Generative State
  const [generativeStrategy, setGenerativeStrategy] = useState<GenerativeStrategy | null>(null)

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
    await new Promise(resolve => setTimeout(resolve, 1500))
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

    const syntheticEvent = (val: string) => ({ target: { value: val } } as ChangeEvent<HTMLInputElement>)

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
      setHistory(prev => {
        // Prevent duplicate saves for same payload
        const last = prev[0]
        if (last && JSON.stringify(last.payload) === JSON.stringify(payload)) {
          return prev
        }
        const newItem: HistoryItem = {
           id: Date.now().toString(),
           timestamp: new Date(),
           payload: payload,
           result: result
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
        structureType: appliedAssumptions.structureType,
        mepLoadWpsm: appliedAssumptions.mepLoadWpsm,
        capRatePercent: appliedFinancials.capRatePercent,
        interestRatePercent: appliedFinancials.interestRatePercent,
        targetMarginPercent: appliedFinancials.targetMarginPercent,
      }
      console.log('FeasibilityWizard: handleSubmit setting payload:', newPayload)
      setPayload(newPayload)
    },
    [addressInput, siteAreaInput, landUseInput, appliedAssumptions, appliedFinancials, setPayload, t],
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
      targetMarginPercent: payload.targetMarginPercent
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

  const handleRestore = useCallback((item: HistoryItem) => {
      // 1. Restore Addresses
      setAddressInput(item.payload.address)
      setSiteAreaInput(item.payload.siteAreaSqm.toString())
      setLandUseInput(item.payload.landUse)

      // 2. Restore Assumptions (via hook methods if exposed, or just set inputs)
      // Since useAssumptions controls its own state, we need to manually reset its internal state
      // or just force the payload.
      // Ideally, the hooks should expose setters, but for now we set the inputs which drives the applied state.
       const syntheticEvent = (val: string) => ({ target: { value: val } } as ChangeEvent<HTMLInputElement>)
       handleAssumptionChange('typFloorToFloorM')(syntheticEvent(item.payload.typFloorToFloorM.toString()))
       handleAssumptionChange('efficiencyRatio')(syntheticEvent(item.payload.efficiencyRatio.toString()))

       // Engineering
       if (item.payload.structureType) {
          handleAssumptionChange('structureType')(syntheticEvent(item.payload.structureType))
       }
       if (item.payload.mepLoadWpsm) {
           handleAssumptionChange('mepLoadWpsm')(syntheticEvent(item.payload.mepLoadWpsm.toString()))
       }

       // Financials
       if (item.payload.capRatePercent) {
           handleFinancialChange('capRatePercent')(syntheticEvent(item.payload.capRatePercent.toString()))
       }
       if (item.payload.interestRatePercent) {
           handleFinancialChange('interestRatePercent')(syntheticEvent(item.payload.interestRatePercent.toString()))
       }
        if (item.payload.targetMarginPercent) {
           handleFinancialChange('targetMarginPercent')(syntheticEvent(item.payload.targetMarginPercent.toString()))
       }

      // 3. Set Payload (triggers re-compute effectively, or just restore result if we want)
      // If we want to view the cached result immediately:
      // setResult(item.result) // We can't set result directly as useFeasibilityCompute owns it.
      // So we just set payload to trigger re-run (or hit cache).
      setPayload(item.payload)
      setHistoryOpen(false)
  }, [handleAssumptionChange, handleFinancialChange, setPayload])


  // Render
  const headerActions = (
    <div className="feasibility-wizard__toolbar">
      <button
        type="button"
        onClick={() => setAiSidebarOpen(true)}
        className="feasibility-wizard__copy"
        style={{ marginRight: '8px', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
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

          {/* New Financial Settings Panel */}
          <FinancialSettingsPanel
             financialInputs={financialInputs}
             financialErrors={financialErrors}
             onFinancialChange={handleFinancialChange}
             t={t}
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
                sx: { borderRadius: 'var(--ob-radius-lg)', overflow: 'hidden' }
              }}
            >
              <DialogTitle sx={{ borderBottom: '1px solid var(--ob-color-border-light)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                 <span>Pack Preview: {packType.charAt(0).toUpperCase() + packType.slice(1)}</span>
                 <Typography variant="caption" sx={{ color: 'text.secondary' }}>LIVE GENERATION</Typography>
              </DialogTitle>
              <DialogContent sx={{ minHeight: '400px', background: '#f5f5f7', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 0 }}>
                 <div style={{
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
                   transition: 'transform 0.3s'
                 }}>
                    <div style={{ width: '100%', height: '180px', background: 'var(--ob-color-bg-surface-secondary)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 'auto' }}>
                       {/* Placeholder for Cover Image */}
                       <span style={{ fontSize: '3rem' }}>🏢</span>
                    </div>
                    <div style={{ padding: '2rem', textAlign: 'center' }}>
                       <Typography variant="h6" gutterBottom>{addressInput || 'Site Address'}</Typography>
                       <Typography variant="body2" color="text.secondary">Optimal Build Professional Pack</Typography>
                       <div style={{ marginTop: '1rem', height: '4px', width: '40px', background: 'var(--ob-color-brand-primary)', marginInline: 'auto' }} />
                    </div>
                    <div style={{ marginTop: 'auto', padding: '1rem', width: '100%', borderTop: '1px solid #eee', display: 'flex', justifyContent: 'space-between' }}>
                       <span style={{ fontSize: '0.7rem', color: '#999' }}>GENERATED: {new Date().toLocaleDateString()}</span>
                       <span style={{ fontSize: '0.7rem', color: '#999' }}>PAGE 1/12</span>
                    </div>
                 </div>
              </DialogContent>
              <DialogActions sx={{ padding: '1rem', borderTop: '1px solid var(--ob-color-border-light)' }}>
                 <Button onClick={() => setIsPreviewOpen(false)} sx={{ color: 'text.secondary' }}>Close</Button>
                 <Button variant="contained" startIcon={<DownloadIcon />} onClick={() => generatePackFn?.(propertyIdFromQuery || 'demo', packType as ProfessionalPackType)}>
                   Download PDF
                 </Button>
              </DialogActions>
            </Dialog>

    </div>
  )

  // Render Maps
  const renderMap = () => (
    <div style={{ height: '100%', width: '100%' }}>
      <PropertyLocationMap
         latitude="1.285" // Default near Singapore CBD
         longitude="103.854"
         interactive
         height={800} // Fill height
         showAmenities={false}
         showHeritage={false}
         onCoordinatesChange={(lat, lon) => console.log('Map coords:', lat, lon)}
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
        renderAddressBar={() => (
          <SmartSearchBar
            value={addressInput}
            onChange={handleAddressChange}
            onSubmit={(e) => {
               e.preventDefault()
               handleSubmit(e)
            }}
            loading={status === 'loading'}
            error={addressError}
            onSuggestionSelect={(suggestion) => {
                setAddressInput(suggestion.address)
                setSiteAreaInput(suggestion.siteArea.toString())
                setLandUseInput(suggestion.zoning)
                // Clear any manual typing error since user selected a valid entry
                setAddressError(null)
            }}
          />

        )}
        renderFooter={() => (
           <div className="feasibility-actions" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <ScenarioFAB
                label={status === 'loading' ? 'Calculating...' : (t('wizard.actions.compute') || 'Run Analysis')}
                onClick={() => {
                   // Trigger submit manually since FAB is outside form
                   const syntheticEvent = { preventDefault: () => {} } as FormEvent<HTMLFormElement>
                   handleSubmit(syntheticEvent)
                }}
                loading={status === 'loading'}
              />
           </div>
        )}
      >
        <div className="feasibility-wizard__sidebar-content">
           {/* Section 1: Site Details (Hidden in favor of Smart Search mostly, but we keep extras) */}
           <div className="feasibility-section">
              <h3>{t('wizard.steps.siteDetails')}</h3>
              <div className="feasibility-form__field">
                 <label className="feasibility-form__label">{t('wizard.form.siteArea')}</label>
                 <input
                   type="number"
                   value={siteAreaInput}
                   onChange={handleSiteAreaChange}
                   placeholder="e.g. 1000"
                   data-testid="site-area-input"
                 />
              </div>
              <div className="feasibility-form__field">
                 <label className="feasibility-form__label">{t('wizard.form.landUse')}</label>
                 <select value={landUseInput} onChange={handleLandUseChange} data-testid="land-use-input">
                   <option value="Mixed Use">Mixed Use</option>
                   <option value="Residential">Residential</option>
                   <option value="Commercial">Commercial</option>
                 </select>
              </div>
           </div>

           {/* Section 2: Assumptions (Accordion Style) */}
           <div className="feasibility-section">
             <AssumptionsPanel
               assumptionInputs={assumptionInputs}
               assumptionErrors={assumptionErrors}
               decimalFormatter={decimalFormatter}
               onAssumptionChange={handleAssumptionChange}
               onResetAssumptions={handleResetAssumptions}
               t={t}
             />
             <FinancialSettingsPanel
                financialInputs={financialInputs}
                financialErrors={financialErrors}
                onFinancialChange={handleFinancialChange}
                t={t}
             />
           </div>

           {/* Section 3: Computing Action - MOVED TO STICKY FOOTER */}

           {/* Section 4: Results (Dynamic) */}
           {result && (
             <div className="feasibility-section">
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

           {/* Section 5: Packs */}
           {result && (
              <div className="feasibility-section">
                  <PackGrid
                     value={packType}
                     onChange={setPackType}
                     options={[
                        { value: 'universal', label: 'Universal Pack', description: 'Site plan & zoning' },
                        { value: 'investment', label: 'Investment Memo', description: 'Financial model & ROI' },
                        { value: 'sales', label: 'Sales Brochure', description: 'Buyer-ready visuals' },
                        { value: 'lease', label: 'Leasing Deck', description: 'Floor efficiency & tenant mix' }
                     ]}
                  />
                  <div style={{ marginTop: '1rem', display: 'flex', justifyContent: 'flex-end' }}>
                     <Button
                       variant="contained"
                       color="primary"
                       onClick={handleGeneratePack}
                       disabled={packGenerating}
                       startIcon={packGenerating ? <span className="scenario-fab__spinner" style={{width: 16, height: 16, border: '2px solid white', borderTopColor: 'transparent'}} /> : <PdfIcon />}
                       sx={{
                         fontFamily: 'var(--ob-font-family-sans)',
                         textTransform: 'none',
                         fontWeight: 600,
                         boxShadow: 'var(--ob-shadow-md)',
                         background: 'var(--ob-color-brand-primary)',
                         '&:hover': { background: 'var(--ob-color-brand-dark)' }
                       }}
                     >
                       {packGenerating ? 'Generating Preview...' : 'Preview & Generate Pack'}
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
                sx: { borderRadius: 'var(--ob-radius-lg)', overflow: 'hidden' }
              }}
            >
              <DialogTitle sx={{ borderBottom: '1px solid var(--ob-color-border-light)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                 <span>Pack Preview: {packType.charAt(0).toUpperCase() + packType.slice(1)}</span>
                 <Typography variant="caption" sx={{ color: 'text.secondary' }}>LIVE GENERATION</Typography>
              </DialogTitle>
              <DialogContent sx={{ minHeight: '400px', background: '#f5f5f7', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 0 }}>
                 <div style={{
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
                   transition: 'transform 0.3s'
                 }}>
                    <div style={{ width: '100%', height: '180px', background: 'var(--ob-color-bg-surface-secondary)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 'auto' }}>
                       {/* Placeholder for Cover Image */}
                       <span style={{ fontSize: '3rem' }}>🏢</span>
                    </div>
                    <div style={{ padding: '2rem', textAlign: 'center' }}>
                       <Typography variant="h6" gutterBottom>{addressInput || 'Site Address'}</Typography>
                       <Typography variant="body2" color="text.secondary">Optimal Build Professional Pack</Typography>
                       <div style={{ marginTop: '1rem', height: '4px', width: '40px', background: 'var(--ob-color-brand-primary)', marginInline: 'auto' }} />
                    </div>
                    <div style={{ marginTop: 'auto', padding: '1rem', width: '100%', borderTop: '1px solid #eee', display: 'flex', justifyContent: 'space-between' }}>
                       <span style={{ fontSize: '0.7rem', color: '#999' }}>GENERATED: {new Date().toLocaleDateString()}</span>
                       <span style={{ fontSize: '0.7rem', color: '#999' }}>PAGE 1/12</span>
                    </div>
                 </div>
              </DialogContent>
              <DialogActions sx={{ padding: '1rem', borderTop: '1px solid var(--ob-color-border-light)' }}>
                 <Button onClick={() => setIsPreviewOpen(false)} sx={{ color: 'text.secondary' }}>Close</Button>
                 <Button variant="contained" startIcon={<DownloadIcon />} onClick={() => generatePackFn?.(propertyIdFromQuery || 'demo', packType as ProfessionalPackType)}>
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
