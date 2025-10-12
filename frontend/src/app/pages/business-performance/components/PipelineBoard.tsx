import type {
  PipelineColumn,
  PipelineDealCard,
  PipelineStageKey,
} from '../types'

const STAGE_LABELS: Record<PipelineStageKey, string> = {
  lead_captured: 'Lead captured',
  qualification: 'Qualification',
  needs_analysis: 'Needs analysis',
  proposal: 'Proposal',
  negotiation: 'Negotiation',
  agreement: 'Agreement',
  due_diligence: 'Due diligence',
  awaiting_closure: 'Awaiting closure',
  closed_won: 'Closed won',
  closed_lost: 'Closed lost',
}

interface PipelineBoardProps {
  columns: PipelineColumn[]
  selectedDealId?: string | null
  onSelectDeal?: (dealId: string) => void
}

export function PipelineBoard({
  columns,
  selectedDealId,
  onSelectDeal,
}: PipelineBoardProps) {
  const handleSelect = (deal: PipelineDealCard) => {
    if (!onSelectDeal) return
    onSelectDeal(deal.id)
  }

  const renderDeal = (deal: PipelineDealCard) => {
    const isSelected = selectedDealId === deal.id
    const cardClass = [
      'bp-pipeline__deal',
      isSelected ? 'bp-pipeline__deal--selected' : '',
      deal.hasDispute ? 'bp-pipeline__deal--flagged' : '',
    ]
      .filter(Boolean)
      .join(' ')

    return (
      <li key={deal.id}>
        <button
          type="button"
          className={cardClass}
          onClick={() => handleSelect(deal)}
        >
          <span className="bp-pipeline__deal-title">{deal.title}</span>
          <span className="bp-pipeline__deal-meta">
            {deal.assetType} • {deal.dealType}
          </span>
          {deal.estimatedValue !== null && (
            <span className="bp-pipeline__deal-value">
              {deal.currency}{' '}
              {deal.estimatedValue.toLocaleString(undefined, {
                maximumFractionDigits: 0,
              })}
            </span>
          )}
          {deal.confidence !== null && (
            <span className="bp-pipeline__deal-confidence">
              Confidence: {(deal.confidence * 100).toFixed(0)}%
            </span>
          )}
          {deal.latestActivity && (
            <span className="bp-pipeline__deal-activity">
              Updated: {deal.latestActivity}
            </span>
          )}
          {deal.hasDispute && (
            <span className="bp-pipeline__deal-badge">Dispute</span>
          )}
        </button>
      </li>
    )
  }

  const renderColumn = (column: PipelineColumn) => {
    const stageLabel = STAGE_LABELS[column.key] ?? column.label
    return (
      <article key={column.key} className="bp-pipeline__column">
        <header className="bp-pipeline__column-header">
          <div>
            <h3>{stageLabel}</h3>
            <p>{column.totalCount} deals</p>
          </div>
          <div className="bp-pipeline__column-metrics">
            {column.totalValue !== null && (
              <span>
                Total:{' '}
                {column.totalValue.toLocaleString(undefined, {
                  maximumFractionDigits: 0,
                })}
              </span>
            )}
            {column.weightedValue !== null && (
              <span>
                Weighted:{' '}
                {column.weightedValue.toLocaleString(undefined, {
                  maximumFractionDigits: 0,
                })}
              </span>
            )}
          </div>
        </header>
        <ul className="bp-pipeline__deal-list">{column.deals.map(renderDeal)}</ul>
      </article>
    )
  }

  return (
    <div className="bp-pipeline" role="list">
      {columns.map(renderColumn)}
    </div>
  )
}

