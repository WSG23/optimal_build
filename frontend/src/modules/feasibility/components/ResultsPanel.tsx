import type { ReactNode } from 'react'

import type {
  BuildableSummary,
  WizardStatus,
  StoredAssetOptimization,
  FinancialSummary,
} from '../types'
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
      {(status === 'idle' || status === 'loading') && (
        <div
          style={{
            position: 'relative',
            height: '100%',
            minHeight: '600px',
            overflow: 'hidden',
            borderRadius: 'var(--ob-radius-sm)',
          }}
        >
          {/* The Blurred Content (Teaser) */}
          <div
            style={{
              filter: 'blur(var(--ob-blur-xs))',
              opacity: 0.5,
              pointerEvents: 'none',
              display: 'grid',
              gap: 'var(--ob-space-300)',
            }}
          >
            {/* Fake Header */}
            <div
              style={{
                height: '120px',
                background: 'var(--ob-color-border-subtle)',
                borderRadius: 'var(--ob-radius-sm)',
              }}
            />

            {/* Fake Grid */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: 'var(--ob-space-300)',
              }}
            >
              <div
                style={{
                  height: '200px',
                  background: 'var(--ob-color-border-subtle)',
                  borderRadius: 'var(--ob-radius-sm)',
                }}
              />
              <div
                style={{
                  height: '200px',
                  background: 'var(--ob-color-border-subtle)',
                  borderRadius: 'var(--ob-radius-sm)',
                }}
              />
            </div>

            <div
              style={{
                height: '300px',
                background: 'var(--ob-color-border-subtle)',
                borderRadius: 'var(--ob-radius-sm)',
              }}
            />
          </div>

          {/* The Lock Overlay */}
          <div
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'flex-end', // Align to bottom for floating CTA
              paddingBottom: 'var(--ob-space-600)',
              // FIXED: Semi-transparent black with blur
              background: 'var(--ob-color-overlay-backdrop)',
              backdropFilter: 'blur(var(--ob-blur-sm))',
              zIndex: 10,
            }}
          >
            {status === 'loading' ? (
              // Scanning Animation
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  marginBottom: 'auto',
                  marginTop: 'auto',
                }}
              >
                <div
                  className="radar-spinner"
                  style={{
                    width: '80px',
                    height: '80px',
                    border: '4px solid var(--ob-color-primary)',
                    borderTopColor: 'transparent',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite',
                  }}
                />
                <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
                <h3
                  style={{
                    marginTop: 'var(--ob-space-300)',
                    fontSize: '1.25rem',
                    fontWeight: 600,
                    color: 'white',
                  }}
                >
                  Analyzing Site Potential...
                </h3>
                <p style={{ color: 'var(--ob-color-text-secondary)' }}>
                  Querying zoning, GFA caps, and market data.
                </p>
              </div>
            ) : (
              // Idle "Floating CTA" State
              <div
                className="glass-panel"
                style={{
                  background: 'rgba(30, 30, 30, 0.6)', // Glassmorphic dark
                  backdropFilter: 'blur(var(--ob-blur-md))',
                  border: '1px solid var(--ob-color-surface-overlay)',
                  padding: '24px 32px',
                  borderRadius: 'var(--ob-radius-sm)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--ob-space-200)',
                  boxShadow: '0 20px 40px var(--ob-color-overlay-backdrop)',
                  transform: 'translateY(0)',
                  animation: 'float 6s ease-in-out infinite',
                }}
              >
                <style>{`
                            @keyframes float {
                                0% { transform: translateY(0px); }
                                50% { transform: translateY(-10px); }
                                100% { transform: translateY(0px); }
                            }
                        `}</style>
                <div
                  style={{
                    background: 'white',
                    borderRadius: '50%',
                    width: '48px',
                    height: '48px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}
                >
                  {/* Small Lock Icon */}
                  <svg
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="black"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                  </svg>
                </div>
                <div>
                  <h3
                    style={{
                      fontSize: '1rem',
                      fontWeight: 600,
                      margin: '0 0 4px 0',
                      color: 'white',
                    }}
                  >
                    Unlock Site Intelligence
                  </h3>
                  <p
                    style={{
                      margin: '0',
                      color: 'var(--ob-color-text-secondary)',
                      fontSize: '0.875rem',
                    }}
                  >
                    Enter an address to visualize potential.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {status === 'error' && (
        <p className="feasibility-results__error" role="alert">
          {errorMessage ?? t('wizard.errors.generic')}
        </p>
      )}

      {(status === 'success' || status === 'partial' || status === 'empty') &&
        result && (
          <div
            className="feasibility-results__content"
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--ob-space-8)',
            }}
          >
            {/* Header / Hero Stats */}
            <header
              className="feasibility-results__header"
              style={{
                marginBottom: 'var(--ob-space-4)',
                animation:
                  'slideUpFade 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards',
                opacity: 0,
                transform: 'translateY(20px)',
              }}
            >
              <style>
                {`
                        @keyframes slideUpFade {
                            from { opacity: 0; transform: translateY(20px); }
                            to { opacity: 1; transform: translateY(0); }
                        }
                    `}
              </style>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr auto',
                  gap: 'var(--ob-space-4)',
                  alignItems: 'start',
                }}
              >
                {/* Zone & Title */}
                <div
                  style={{
                    background: 'white',
                    padding: 'var(--ob-space-5)',
                    borderRadius: 'var(--ob-radius-lg)',
                    border: '1px solid var(--ob-color-border-premium)',
                    boxShadow: 'var(--ob-depth-md)',
                  }}
                >
                  <span
                    className="text-eyebrow"
                    style={{
                      display: 'block',
                      marginBottom: 'var(--ob-space-50)',
                    }}
                  >
                    OPTIMIZED FOR
                  </span>
                  <h2
                    style={{
                      fontSize: '2rem',
                      fontWeight: 700,
                      margin: 0,
                      letterSpacing: '-0.02em',
                      background: 'linear-gradient(45deg, #111827, #374151)',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                    }}
                    data-testid="zone-code"
                  >
                    {result.zoneCode ?? t('wizard.results.zoneUnknown')}
                  </h2>
                  <div
                    data-testid="overlay-badges"
                    style={{
                      marginTop: 'var(--ob-space-100)',
                      display: 'flex',
                      gap: 'var(--ob-space-100)',
                    }}
                  >
                    {result.overlays.map((overlay) => (
                      <span
                        key={overlay}
                        style={{
                          fontSize: '0.7rem',
                          fontWeight: 600,
                          padding: '2px 8px',
                          borderRadius: 'var(--ob-radius-sm)',
                          background: '#EFF6FF',
                          color: '#2563EB',
                          border: '1px solid #BFDBFE',
                        }}
                      >
                        {overlay}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Summary Metric Card (e.g. Total GFA) */}
                <div
                  style={{
                    background: '#1F2937',
                    color: 'white',
                    padding: 'var(--ob-space-5)',
                    borderRadius: 'var(--ob-radius-lg)',
                    minWidth: '200px',
                    boxShadow:
                      '0 10px 15px -3px var(--ob-color-action-active-light), 0 4px 6px -2px var(--ob-color-action-hover-light)',
                  }}
                >
                  <span
                    style={{
                      fontSize: '0.75rem',
                      opacity: 0.8,
                      textTransform: 'uppercase',
                      letterSpacing: '0.05em',
                    }}
                  >
                    Max GFA Potential
                  </span>
                  <div
                    style={{
                      fontSize: '2.25rem',
                      fontWeight: 700,
                      lineHeight: 1.1,
                      marginTop: 'var(--ob-space-50)',
                    }}
                  >
                    {numberFormatter.format(result.metrics.gfaCapM2)}
                    <span
                      style={{
                        fontSize: '1rem',
                        fontWeight: 400,
                        opacity: 0.6,
                        marginLeft: 'var(--ob-space-50)',
                      }}
                    >
                      m²
                    </span>
                  </div>
                </div>
              </div>
            </header>

            {/* Metrics Grid */}
            <MetricsView
              result={result}
              numberFormatter={numberFormatter}
              t={t}
            />

            <AssetMixView
              capturedAssetMix={capturedAssetMix}
              capturedFinancialSummary={capturedFinancialSummary}
              numberFormatter={numberFormatter}
              oneDecimalFormatter={oneDecimalFormatter}
            />

            <AdvisoryView hints={result.advisoryHints ?? []} t={t} />

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
                <ul
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 'var(--ob-space-3)',
                  }}
                >
                  {result.rules.map((rule) => (
                    <li
                      key={rule.id}
                      className="feasibility-citation"
                      style={{
                        padding: 'var(--ob-space-3)',
                        borderLeft: '2px solid var(--ob-color-accent)',
                        background: 'white',
                        borderRadius:
                          '0 var(--ob-radius-md) var(--ob-radius-md) 0',
                      }}
                    >
                      <div
                        className="feasibility-citation__meta"
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          marginBottom: 'var(--ob-space-1)',
                        }}
                      >
                        <span
                          className="feasibility-citation__authority"
                          style={{ fontWeight: 600, fontSize: '0.75rem' }}
                        >
                          {rule.authority}
                        </span>
                        <span
                          className="feasibility-citation__clause"
                          style={{
                            color: 'var(--ob-color-text-muted)',
                            fontSize: '0.75rem',
                          }}
                        >
                          {rule.provenance.clauseRef ??
                            t('wizard.citations.unknownClause')}
                        </span>
                      </div>
                      <p
                        className="feasibility-citation__parameter"
                        style={{
                          fontFamily: 'monospace',
                          fontSize: '0.8125rem',
                        }}
                      >
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
