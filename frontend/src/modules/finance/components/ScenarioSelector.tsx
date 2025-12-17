/**
 * ScenarioSelector - Horizontal button group for scenario selection
 *
 * Follows UI_STANDARDS.md:
 * - Uses design tokens for spacing, radius, typography
 * - Dark inverted active state (text.primary bg, background.paper text)
 * - Two-line button: uppercase label + description
 */

import { Button, Typography, useTheme, alpha } from '@mui/material'

import type { FinanceScenarioSummary } from '../../../api/finance'
import { GlassCard } from '../../../components/canonical/GlassCard'

interface ScenarioSelectorProps {
  scenarios: FinanceScenarioSummary[]
  activeId: number | null
  onSelect: (scenarioId: number) => void
}

export function ScenarioSelector({
  scenarios,
  activeId,
  onSelect,
}: ScenarioSelectorProps) {
  const theme = useTheme()

  if (scenarios.length === 0) {
    return null
  }

  return (
    <GlassCard
      sx={{
        display: 'inline-flex',
        flexWrap: 'wrap',
        p: 'var(--ob-space-025)',
        mb: 'var(--ob-space-150)',
        gap: 'var(--ob-space-025)',
      }}
    >
      {scenarios.map((scenario) => {
        const isActive = scenario.scenarioId === activeId
        return (
          <Button
            key={scenario.scenarioId}
            onClick={() => onSelect(scenario.scenarioId)}
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'flex-start',
              px: 'var(--ob-space-100)',
              py: 'var(--ob-space-050)',
              borderRadius: 'var(--ob-radius-xs)',
              textTransform: 'none',
              minWidth: 120,
              bgcolor: isActive ? 'text.primary' : 'transparent',
              color: isActive ? 'background.paper' : 'text.secondary',
              boxShadow: isActive ? theme.shadows[2] : 'none',
              transition: 'all 0.2s ease',
              '&:hover': {
                bgcolor: isActive
                  ? 'text.primary'
                  : alpha(theme.palette.text.primary, 0.06),
                color: isActive ? 'background.paper' : 'text.primary',
              },
            }}
          >
            <Typography
              component="span"
              sx={{
                fontSize: 'var(--ob-font-size-2xs)',
                textTransform: 'uppercase',
                letterSpacing: 'var(--ob-letter-spacing-wider)',
                opacity: 0.8,
                mb: 'var(--ob-space-025)',
              }}
            >
              {scenario.scenarioName}
            </Typography>
            <Typography
              component="span"
              sx={{
                fontSize: 'var(--ob-font-size-md)',
                fontWeight: 500,
              }}
            >
              {scenario.isPrimary ? 'Base Case' : 'Scenario'}
            </Typography>
          </Button>
        )
      })}
    </GlassCard>
  )
}

export default ScenarioSelector
