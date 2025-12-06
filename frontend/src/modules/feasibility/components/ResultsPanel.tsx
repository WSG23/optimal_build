import type { ReactNode } from 'react'

import type { BuildableSummary, WizardStatus, StoredAssetOptimization, FinancialSummary } from '../types'
import { MetricsView } from './MetricsView'
import { AssetMixView } from './AssetMixView'
import { AdvisoryView } from './AdvisoryView'
import { SkeletonLoader } from '../../../components/feedback/SkeletonLoader'

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
        <p className="feasibility-results__placeholder">{t('wizard.states.idle')}</p>
      )}

      {status === 'loading' && (
        <div className="feasibility-results__skeleton" role="status">
          <SkeletonLoader variant="card" count={1} />
        </div>
      )}

      {status === 'error' && (
        <p className="feasibility-results__error" role="alert">
          {errorMessage ?? t('wizard.errors.generic')}
        </p>
      )}

      {(status === 'success' || status === 'partial' || status === 'empty') &&
        result && (
          <div className="feasibility-results__content">
            <header className="feasibility-results__header">
              <div>
                <span className="feasibility-results__label">
                  {t('wizard.results.zone')}
                </span>
                <span className="feasibility-results__value" data-testid="zone-code">
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
                    <span key={overlay} className="feasibility-results__badge">
                      {overlay}
                    </span>
                  ))}
                </div>
              </div>
            </header>

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
