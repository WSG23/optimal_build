/**
 * ScenarioFocusSection - Scenario filter buttons for developer results
 *
 * Extracted from DeveloperResults to reduce file size.
 */

import { Box, Typography } from '@mui/material'

import type { DevelopmentScenario } from '../../../../api/agents'
import { Button } from '../../../../components/canonical/Button'

export interface ScenarioFocusSectionProps {
  activeScenario: DevelopmentScenario | 'all'
  selectedScenarios: DevelopmentScenario[]
  defaultRecommendationLabel: string
  formatScenarioLabel: (scenario: DevelopmentScenario | 'all' | null) => string
  onSelectAll: () => void
  onSelectScenario: (scenario: DevelopmentScenario) => void
}

export function ScenarioFocusSection({
  activeScenario,
  selectedScenarios,
  defaultRecommendationLabel,
  formatScenarioLabel,
  onSelectAll,
  onSelectScenario,
}: ScenarioFocusSectionProps) {
  return (
    <section className="site-acquisition__scenario-focus">
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 'var(--ob-space-150)',
        }}
      >
        <Typography
          variant="h6"
          sx={{
            fontWeight: 'var(--ob-font-weight-semibold)',
            color: 'var(--ob-color-text-primary)',
          }}
        >
          Scenario Focus
        </Typography>
        <Box
          sx={{
            display: 'flex',
            gap: 'var(--ob-space-050)',
            alignItems: 'center',
            flexWrap: 'wrap',
          }}
        >
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-xs)',
              color: 'text.secondary',
            }}
          >
            Recommended: {defaultRecommendationLabel}
          </Typography>
          <Button
            key="all"
            variant={activeScenario === 'all' ? 'primary' : 'ghost'}
            size="sm"
            onClick={onSelectAll}
          >
            All Scenarios
          </Button>
          {selectedScenarios.map((scenario) => (
            <Button
              key={scenario}
              variant={activeScenario === scenario ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => onSelectScenario(scenario)}
            >
              {formatScenarioLabel(scenario)}
            </Button>
          ))}
        </Box>
      </Box>
    </section>
  )
}
