import type { ReactNode } from 'react'

import type { BuildableSummary, WizardStatus, StoredAssetOptimization, FinancialSummary } from '../types'
import { MetricsView } from './MetricsView'
import { AssetMixView } from './AssetMixView'
import { AdvisoryView } from './AdvisoryView'

interface ResultsPanelProps {
  status: WizardStatus
  result: BuildableSummary | null
  errorMessage: string | null
  capturedAssetMix: StoredAssetOptimization[]
  capturedFinancialSummary: FinancialSummary | null
  numberFormatter: Intl.NumberFormat
  oneDecimalFormatter: Intl.NumberFormat
  t: (key: string, options?: Record<string, unknown>) => string
}

function renderProvenanceBadge(
  provenance: BuildableSummary['rules'][number]['provenance'],
  t: (key: string, options?: Record<string, unknown>) => string,
): ReactNode {
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

export function ResultsPanel({
  status,
  result,
  errorMessage,
  capturedAssetMix,
  capturedFinancialSummary,
  numberFormatter,
  oneDecimalFormatter,
  t,
}: ResultsPanelProps) {
  return (
    <section
      className="feasibility-results"
      aria-live="polite"
      aria-busy={status === 'loading'}
    >
      {status === 'idle' && (
        <div style={{ textAlign: 'center', padding: 'var(--ob-space-12) var(--ob-space-4)', color: 'var(--ob-color-text-muted)' }}>
             <p>{t('wizard.states.idle')}</p>
        </div>
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

      {(status === 'success' || status === 'partial' || status === 'empty') &&
        result && (
          <div className="feasibility-results__content" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--ob-space-8)' }}>

            {/* Header / Key Info */}
            <header className="feasibility-results__header" style={{
                background: 'white',
                padding: 'var(--ob-space-5)',
                borderRadius: 'var(--ob-radius-lg)',
                border: '1px solid var(--ob-color-border-premium)',
                boxShadow: 'var(--ob-depth-sm)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
            }}>
              <div>
                <span className="text-eyebrow" style={{ display: 'block', marginBottom: 'var(--ob-space-1)' }}>
                  {t('wizard.results.zone')}
                </span>
                <span className="text-display" data-testid="zone-code">
                  {result.zoneCode ?? t('wizard.results.zoneUnknown')}
                </span>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span className="text-eyebrow" style={{ display: 'block', marginBottom: 'var(--ob-space-1)' }}>
                  {t('wizard.results.overlays')}
                </span>
                <div
                  className="feasibility-results__overlays"
                  data-testid="overlay-badges"
                  style={{ display: 'flex', gap: 'var(--ob-space-2)', justifyContent: 'flex-end', flexWrap: 'wrap' }}
                >
                  {result.overlays.length === 0 && (
                    <span className="feasibility-results__badge">
                      {t('wizard.results.none')}
                    </span>
                  )}
                  {result.overlays.map((overlay) => (
                    <span key={overlay}
                          className="feasibility-results__badge"
                          style={{
                              background: 'var(--ob-color-accent-light)',
                              color: 'var(--ob-color-accent)',
                              fontSize: '0.75rem',
                              fontWeight: 600,
                              padding: '4px 8px',
                              borderRadius: '4px'
                          }}>
                      {overlay}
                    </span>
                  ))}
                </div>
              </div>
            </header>

            {/* Metrics Grid */}
            <MetricsView result={result} numberFormatter={numberFormatter} t={t} />

            <AssetMixView
              capturedAssetMix={capturedAssetMix}
              capturedFinancialSummary={capturedFinancialSummary}
              numberFormatter={numberFormatter}
              oneDecimalFormatter={oneDecimalFormatter}
            />

            <AdvisoryView hints={result.advisoryHints ?? []} t={t} />

            {status === 'empty' && (
              <p className="feasibility-results__empty">{t('wizard.states.empty')}</p>
            )}

            {status === 'partial' && result.zoneCode && (
              <p className="feasibility-results__partial">
                {t('wizard.states.partial')}
              </p>
            )}

            {result.rules.length > 0 && (
              <section className="feasibility-citations" data-testid="citations">
                <h3>{t('wizard.citations.title')}</h3>
                <ul style={{ display: 'flex', flexDirection: 'column', gap: 'var(--ob-space-3)' }}>
                  {result.rules.map((rule) => (
                    <li key={rule.id} className="feasibility-citation" style={{
                        padding: 'var(--ob-space-3)',
                        borderLeft: '2px solid var(--ob-color-accent)',
                        background: 'white',
                        borderRadius: '0 var(--ob-radius-md) var(--ob-radius-md) 0'
                    }}>
                      <div className="feasibility-citation__meta" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--ob-space-1)' }}>
                        <span className="feasibility-citation__authority" style={{ fontWeight: 600, fontSize: '0.75rem' }}>
                          {rule.authority}
                        </span>
                        <span className="feasibility-citation__clause" style={{ color: 'var(--ob-color-text-muted)', fontSize: '0.75rem' }}>
                          {rule.provenance.clauseRef ??
                            t('wizard.citations.unknownClause')}
                        </span>
                      </div>
                      <p className="feasibility-citation__parameter" style={{ fontFamily: 'monospace', fontSize: '0.8125rem' }}>
                        {`${rule.parameterKey} ${rule.operator} ${rule.value}${
                          rule.unit ? ` ${rule.unit}` : ''
                        }`}
                      </p>
                      {renderProvenanceBadge(rule.provenance, t)}
                    </li>
                  ))}
                </ul>
              </section>
            )}
          </div>
        )}
    </section>
  )
}
