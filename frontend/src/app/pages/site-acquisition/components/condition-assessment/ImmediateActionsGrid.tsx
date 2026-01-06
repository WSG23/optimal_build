/**
 * Immediate Actions Grid Component
 *
 * Displays a 2x2 grid of action cards with:
 * - Title (--ob-font-size-sm, fontWeight: 700)
 * - Description (--ob-font-size-2xs, text.secondary)
 * - Priority badge (StatusChip with semantic status)
 *
 * Follows AI Studio's compact action card pattern.
 */

import { Box, Typography, Grid } from '@mui/material'
import { StatusChip } from '../../../../../components/canonical'

// ============================================================================
// Types
// ============================================================================

export type ActionPriority = 'critical' | 'high' | 'medium' | 'low'

export interface ImmediateAction {
  id: string
  title: string
  description: string
  priority: ActionPriority
}

export interface ImmediateActionsGridProps {
  /** Array of actions to display */
  actions: ImmediateAction[]
  /** Optional click handler for action cards */
  onActionClick?: (actionId: string) => void
}

// ============================================================================
// Priority to StatusChip mapping
// ============================================================================

const priorityToStatus = {
  critical: 'error',
  high: 'warning',
  medium: 'info',
  low: 'neutral',
} as const

const priorityLabels = {
  critical: 'Critical',
  high: 'High',
  medium: 'Medium',
  low: 'Low',
} as const

// ============================================================================
// Component
// ============================================================================

export function ImmediateActionsGrid({
  actions,
  onActionClick,
}: ImmediateActionsGridProps) {
  if (actions.length === 0) {
    return null
  }

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--ob-space-100)',
      }}
    >
      <Typography
        variant="h4"
        sx={{
          m: 0,
          // Additional bottom margin for visual separation from cards
          mb: 'var(--ob-space-050)',
          fontSize: 'var(--ob-font-size-sm)',
          fontWeight: 700,
          color: 'text.primary',
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
        }}
      >
        Immediate System Actions
      </Typography>

      <Grid container spacing={1}>
        {actions.slice(0, 4).map((action) => (
          <Grid item xs={12} sm={6} key={action.id}>
            <Box
              className="immediate-action-card"
              onClick={
                onActionClick ? () => onActionClick(action.id) : undefined
              }
              sx={{
                p: 'var(--ob-space-125)',
                // Glass surface per Sibling Card Surface Standard
                background: 'var(--ob-surface-glass-1)',
                backdropFilter: 'blur(var(--ob-blur-md))',
                WebkitBackdropFilter: 'blur(var(--ob-blur-md))',
                borderRadius: 'var(--ob-radius-sm)',
                border: '1px solid var(--ob-color-border-subtle)',
                cursor: onActionClick ? 'pointer' : 'default',
                transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--ob-space-050)',
                minHeight: '72px',
                // Cyan hover state per Card Interaction States
                '&:hover': {
                  borderColor: 'var(--ob-color-neon-cyan)',
                  boxShadow: '0 0 8px var(--ob-color-neon-cyan-muted)',
                },
              }}
            >
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  gap: 'var(--ob-space-075)',
                }}
              >
                <Typography
                  sx={{
                    fontSize: 'var(--ob-font-size-sm)',
                    fontWeight: 700,
                    color: 'text.primary',
                    lineHeight: 1.3,
                    flex: 1,
                  }}
                >
                  {action.title}
                </Typography>
                <StatusChip
                  status={priorityToStatus[action.priority]}
                  size="sm"
                >
                  {priorityLabels[action.priority]}
                </StatusChip>
              </Box>
              {/* Only render description if it exists and differs from title */}
              {action.description && (
                <Typography
                  sx={{
                    fontSize: 'var(--ob-font-size-2xs)',
                    color: 'text.secondary',
                    lineHeight: 1.4,
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden',
                  }}
                >
                  {action.description}
                </Typography>
              )}
            </Box>
          </Grid>
        ))}
      </Grid>
    </Box>
  )
}
