import { useMemo, useState } from 'react'
import { PipelineBoard } from './components/PipelineBoard'
import { DealInsightsPanel } from './components/DealInsightsPanel'
import { AnalyticsPanel } from './components/AnalyticsPanel'
import { RoiPanel } from './components/RoiPanel'
import {
  MOCK_BENCHMARKS,
  MOCK_COMMISSIONS,
  MOCK_DEAL,
  MOCK_METRICS,
  MOCK_PIPELINE_COLUMNS,
  MOCK_ROI,
  MOCK_TIMELINE,
  MOCK_TREND,
} from './mockData'

export function BusinessPerformancePage() {
  const lastSnapshot = useMemo(
    () => new Date().toLocaleDateString(undefined, { dateStyle: 'medium' }),
    [],
  )
  const columns = useMemo(() => [...MOCK_PIPELINE_COLUMNS], [])
  const [selectedDealId, setSelectedDealId] = useState<string | null>(
    MOCK_DEAL.id,
  )

  const selectedDeal = useMemo(() => {
    if (!selectedDealId) return null
    return MOCK_DEAL.id === selectedDealId ? MOCK_DEAL : null
  }, [selectedDealId])

  return (
    <div className="bp-page">
      <section className="bp-page__summary">
        <div className="bp-summary-card">
          <header>
            <span className="bp-summary-card__label">Last snapshot</span>
            <span className="bp-summary-card__value">{lastSnapshot}</span>
          </header>
          <p className="bp-summary-card__meta">
            Snapshot jobs run nightly. Manual refresh will be available shortly.
          </p>
        </div>
        <div className="bp-summary-card">
          <header>
            <span className="bp-summary-card__label">Open pipeline value</span>
            <span className="bp-summary-card__value">SGD 18.4M</span>
          </header>
          <p className="bp-summary-card__meta">
            Weighted pipeline: <strong>SGD 9.7M</strong> (confidence-adjusted).
          </p>
        </div>
        <div className="bp-summary-card">
          <header>
            <span className="bp-summary-card__label">ROI projects tracked</span>
            <span className="bp-summary-card__value">
              {MOCK_ROI.projectCount}
            </span>
          </header>
          <p className="bp-summary-card__meta">
            Automation ROI derives from overlay workflows and audit metrics.
          </p>
        </div>
      </section>

      <div className="bp-page__layout">
        <section className="bp-page__pipeline">
          <PipelineBoard
            columns={columns}
            selectedDealId={selectedDealId}
            onSelectDeal={setSelectedDealId}
          />
        </section>
        <aside className="bp-page__sidebar">
          <DealInsightsPanel
            deal={selectedDeal}
            timeline={MOCK_TIMELINE}
            commissions={MOCK_COMMISSIONS}
          />
          <AnalyticsPanel
            metrics={MOCK_METRICS}
            trend={MOCK_TREND}
            benchmarks={MOCK_BENCHMARKS}
          />
          <RoiPanel summary={MOCK_ROI} />
        </aside>
      </div>
    </div>
  )
}

