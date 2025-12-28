/**
 * CapitalStackScenarioTabs - Horizontal underlined tabs for scenario switching
 *
 * Premium cyber aesthetic:
 * - Horizontal tabs with "Scenario A: Base Case" format
 * - Active tab has cyan underline with glow
 * - Inactive tabs have transparent border
 *
 * Follows UI_STANDARDS.md for design tokens.
 */

import { Box, Button } from '@mui/material'

import { useTranslation } from '../../../i18n'
import type { FinanceScenarioSummary } from '../../../api/finance'

interface CapitalStackScenarioTabsProps {
  scenarios: FinanceScenarioSummary[]
  activeId: number | null
  onSelect: (id: number) => void
}

export function CapitalStackScenarioTabs({
  scenarios,
  activeId,
  onSelect,
}: CapitalStackScenarioTabsProps) {
  const { t } = useTranslation()

  if (scenarios.length === 0) {
    return null
  }

  return (
    <Box
      sx={{
        borderBottom: 1,
        borderColor: 'divider',
        mb: 'var(--ob-space-150)',
      }}
    >
      <Box
        sx={{
          display: 'flex',
          gap: 'var(--ob-space-200)',
          ml: '-var(--ob-space-025)',
        }}
      >
        {scenarios.map((scenario) => {
          const isActive = scenario.scenarioId === activeId
          return (
            <Button
              key={scenario.scenarioId}
              onClick={() => onSelect(scenario.scenarioId)}
              sx={{
                py: 'var(--ob-space-100)',
                px: 'var(--ob-space-025)',
                borderRadius: 'var(--ob-radius-none)',
                borderBottom: 2,
                borderColor: isActive
                  ? 'var(--ob-color-neon-cyan)'
                  : 'transparent',
                color: isActive
                  ? 'var(--ob-color-neon-cyan)'
                  : 'text.secondary',
                fontWeight: 500,
                fontSize: 'var(--ob-font-size-sm)',
                textTransform: 'none',
                minWidth: 'auto',
                whiteSpace: 'nowrap',
                transition: 'color 0.2s ease, border-color 0.2s ease',
                ...(isActive && {
                  textShadow: 'var(--ob-glow-neon-text)',
                }),
                '&:hover': {
                  color: isActive
                    ? 'var(--ob-color-neon-cyan)'
                    : 'text.primary',
                  bgcolor: 'transparent',
                  borderColor: isActive
                    ? 'var(--ob-color-neon-cyan)'
                    : 'divider',
                },
              }}
            >
              {scenario.scenarioName}:{' '}
              {scenario.description || t('finance.capitalStack.baseCase')}
            </Button>
          )
        })}
      </Box>
    </Box>
  )
}

export default CapitalStackScenarioTabs
