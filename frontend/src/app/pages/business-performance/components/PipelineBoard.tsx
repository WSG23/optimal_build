import { useMemo, useState } from 'react'
import DragIndicatorIcon from '@mui/icons-material/DragIndicator'
import {
  Box,
  ButtonBase,
  Chip,
  LinearProgress,
  Paper,
  Stack,
  Tooltip,
  Typography,
} from '@mui/material'
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
  onStageChange?: (dealId: string, toStage: PipelineStageKey) => void
  movingDealId?: string | null
}

export function PipelineBoard({
  columns,
  selectedDealId,
  onSelectDeal,
  onStageChange,
  movingDealId,
}: PipelineBoardProps) {
  const [draggedDeal, setDraggedDeal] = useState<{
    id: string
    stage: PipelineStageKey
  } | null>(null)
  const [activeDropStage, setActiveDropStage] = useState<PipelineStageKey | null>(
    null,
  )

  const stageOrder = useMemo(
    () => columns.map((column) => column.key),
    [columns],
  )

  const handleDrop = (stage: PipelineStageKey) => {
    if (!draggedDeal) return
    if (stage === draggedDeal.stage) {
      setDraggedDeal(null)
      setActiveDropStage(null)
      return
    }
    onStageChange?.(draggedDeal.id, stage)
    setDraggedDeal(null)
    setActiveDropStage(null)
  }

  const handleSelect = (deal: PipelineDealCard) => {
    if (!onSelectDeal) return
    onSelectDeal(deal.id)
  }

  const renderDeal = (deal: PipelineDealCard, stageKey: PipelineStageKey) => {
    const isSelected = selectedDealId === deal.id
    const cardClass = [
      'bp-pipeline__deal',
      isSelected ? 'bp-pipeline__deal--selected' : '',
      deal.hasDispute ? 'bp-pipeline__deal--flagged' : '',
    ]
      .filter(Boolean)
      .join(' ')

    const stageIndex = stageOrder.indexOf(stageKey)
    const progress = stageIndex >= 0 ? ((stageIndex + 1) / stageOrder.length) * 100 : 0
    const isMoving = movingDealId === deal.id

    return (
      <li key={deal.id}>
        <ButtonBase
          className={cardClass}
          onClick={() => handleSelect(deal)}
          draggable
          onDragStart={() => setDraggedDeal({ id: deal.id, stage: stageKey })}
          onDragEnd={() => {
            setDraggedDeal(null)
            setActiveDropStage(null)
          }}
          aria-grabbed={draggedDeal?.id === deal.id}
          focusRipple
        >
          <Paper elevation={isSelected ? 6 : 1} className="bp-pipeline__deal-surface">
            <Stack direction="row" spacing={1} alignItems="center">
              <DragIndicatorIcon fontSize="small" className="bp-pipeline__deal-handle" />
              <Typography variant="subtitle1" className="bp-pipeline__deal-title">
                {deal.title}
              </Typography>
            </Stack>
            <Typography variant="body2" color="text.secondary" className="bp-pipeline__deal-meta">
              {deal.assetType} • {deal.dealType}
            </Typography>
            {deal.estimatedValue !== null && (
              <Typography variant="h6" className="bp-pipeline__deal-value">
                {deal.currency}{' '}
                {deal.estimatedValue.toLocaleString(undefined, {
                  maximumFractionDigits: 0,
                })}
              </Typography>
            )}
            <Stack direction="row" spacing={1} className="bp-pipeline__deal-tags">
              {deal.confidence !== null && (
                <Chip
                  size="small"
                  color="primary"
                  label={`Confidence ${(deal.confidence * 100).toFixed(0)}%`}
                />
              )}
              {deal.latestActivity && (
                <Chip
                  size="small"
                  variant="outlined"
                  label={`Updated ${deal.latestActivity}`}
                />
              )}
              {deal.hasDispute && <Chip size="small" color="error" label="Dispute" />}
            </Stack>
            <Tooltip title={`Progress ${(progress || 0).toFixed(0)}%`} placement="top">
              <LinearProgress
                variant={progress ? 'determinate' : 'indeterminate'}
                value={progress || undefined}
                className="bp-pipeline__progress"
              />
            </Tooltip>
            {isMoving && (
              <Typography variant="caption" className="bp-pipeline__deal-moving">
                Updating stage…
              </Typography>
            )}
          </Paper>
        </ButtonBase>
      </li>
    )
  }

  const renderColumn = (column: PipelineColumn) => {
    const stageLabel = STAGE_LABELS[column.key] ?? column.label
    const columnIndex = stageOrder.indexOf(column.key)
    const stageProgress =
      columnIndex >= 0 ? ((columnIndex + 1) / stageOrder.length) * 100 : 0
    const isDropTarget = activeDropStage === column.key

    return (
      <Paper
        key={column.key}
        component="article"
        className={`bp-pipeline__column ${
          isDropTarget ? 'bp-pipeline__column--dropping' : ''
        }`}
        elevation={isDropTarget ? 8 : 2}
        onDragOver={(event) => {
          if (!draggedDeal) return
          event.preventDefault()
          setActiveDropStage(column.key)
        }}
        onDragLeave={() => {
          if (activeDropStage === column.key) {
            setActiveDropStage(null)
          }
        }}
        onDrop={(event) => {
          event.preventDefault()
          handleDrop(column.key)
        }}
      >
        <Box className="bp-pipeline__column-header">
          <div>
            <Typography variant="h6">{stageLabel}</Typography>
            <Typography variant="body2" color="text.secondary">
              {column.totalCount} deals
            </Typography>
          </div>
          <div className="bp-pipeline__column-metrics">
            {column.totalValue !== null && (
              <Typography variant="body2">
                Total{' '}
                {column.totalValue.toLocaleString(undefined, {
                  maximumFractionDigits: 0,
                })}
              </Typography>
            )}
            {column.weightedValue !== null && (
              <Typography variant="body2">
                Weighted{' '}
                {column.weightedValue.toLocaleString(undefined, {
                  maximumFractionDigits: 0,
                })}
              </Typography>
            )}
          </div>
        </Box>
        <LinearProgress
          variant="determinate"
          value={stageProgress}
          className="bp-pipeline__column-progress"
        />
        <ul className="bp-pipeline__deal-list">
          {column.deals.length === 0 ? (
            <li className="bp-pipeline__empty">Drag a deal here to start.</li>
          ) : (
            column.deals.map((deal) => renderDeal(deal, column.key))
          )}
        </ul>
      </Paper>
    )
  }

  return (
    <div className="bp-pipeline" role="list">
      {columns.map(renderColumn)}
    </div>
  )
}
