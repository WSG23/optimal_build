import React, { useMemo, useState } from 'react'
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

interface DealCardProps {
  deal: PipelineDealCard
  stageKey: PipelineStageKey
  isSelected: boolean
  isMoving: boolean
  isDragged: boolean
  progress: number
  onSelect: (deal: PipelineDealCard) => void
  onDragStart: (id: string, stage: PipelineStageKey) => void
  onDragEnd: () => void
}

const DealCard = React.memo(function DealCard({
  deal,
  stageKey,
  isSelected,
  isMoving,
  isDragged,
  progress,
  onSelect,
  onDragStart,
  onDragEnd,
}: DealCardProps) {
  const cardClass = [
    'bp-pipeline__deal',
    isSelected ? 'bp-pipeline__deal--selected' : '',
    deal.hasDispute ? 'bp-pipeline__deal--flagged' : '',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <li>
      <ButtonBase
        className={cardClass}
        onClick={() => onSelect(deal)}
        draggable
        onDragStart={() => onDragStart(deal.id, stageKey)}
        onDragEnd={onDragEnd}
        aria-grabbed={isDragged}
        focusRipple
      >
        <Paper
          elevation={isSelected ? 6 : 1}
          className="bp-pipeline__deal-surface"
        >
          <Stack direction="row" spacing={1} alignItems="center">
            <DragIndicatorIcon
              fontSize="small"
              className="bp-pipeline__deal-handle"
            />
            <Typography variant="subtitle1" className="bp-pipeline__deal-title">
              {deal.title}
            </Typography>
          </Stack>
          <Typography
            variant="body2"
            color="text.secondary"
            className="bp-pipeline__deal-meta"
          >
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
            {deal.hasDispute && (
              <Chip size="small" color="error" label="Dispute" />
            )}
          </Stack>
          <Tooltip
            title={`Progress ${(progress || 0).toFixed(0)}%`}
            placement="top"
          >
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
})

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
  const [activeDropStage, setActiveDropStage] =
    useState<PipelineStageKey | null>(null)

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

  const handleDragStart = (id: string, stage: PipelineStageKey) => {
    setDraggedDeal({ id, stage })
  }

  const handleDragEnd = () => {
    setDraggedDeal(null)
    setActiveDropStage(null)
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
            column.deals.map((deal) => {
              const stageIndex = stageOrder.indexOf(column.key)
              const progress =
                stageIndex >= 0
                  ? ((stageIndex + 1) / stageOrder.length) * 100
                  : 0
              return (
                <DealCard
                  key={deal.id}
                  deal={deal}
                  stageKey={column.key}
                  isSelected={selectedDealId === deal.id}
                  isMoving={movingDealId === deal.id}
                  isDragged={draggedDeal?.id === deal.id}
                  progress={progress}
                  onSelect={handleSelect}
                  onDragStart={handleDragStart}
                  onDragEnd={handleDragEnd}
                />
              )
            })
          )}
        </ul>
      </Paper>
    )
  }

  const totalDeals = useMemo(
    () => columns.reduce((sum, col) => sum + col.deals.length, 0),
    [columns],
  )

  if (totalDeals === 0) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          py: 'var(--ob-space-400)',
          px: 'var(--ob-space-200)',
        }}
      >
        <Typography
          variant="h6"
          sx={{
            color: 'var(--ob-color-text-secondary)',
            mb: 'var(--ob-space-050)',
          }}
        >
          No deals in the pipeline yet
        </Typography>
        <Typography
          variant="body2"
          sx={{ color: 'var(--ob-color-text-secondary)' }}
        >
          Create your first deal to get started.
        </Typography>
      </Box>
    )
  }

  return (
    <div className="bp-pipeline" role="list">
      {columns.map(renderColumn)}
    </div>
  )
}
