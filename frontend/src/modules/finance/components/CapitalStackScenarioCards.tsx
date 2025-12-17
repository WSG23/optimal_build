/**
 * CapitalStackScenarioCards - Vertical scenario selector cards
 *
 * Matches Gemini design:
 * - Vertical list of scenario cards
 * - Active state: blue-50 background, ring, shadow, blue dot indicator
 * - Preview button on active card
 * - "SELECT SCENARIO" header
 *
 * Follows UI_STANDARDS.md for design tokens.
 */

import { Box, Button, Typography, useTheme, alpha } from '@mui/material'

import { useTranslation } from '../../../i18n'
import type { FinanceScenarioSummary } from '../../../api/finance'

interface CapitalStackScenarioCardsProps {
  scenarios: FinanceScenarioSummary[]
  activeId: number | null
  onSelect: (id: number) => void
  onPreview?: (scenario: FinanceScenarioSummary) => void
}

export function CapitalStackScenarioCards({
  scenarios,
  activeId,
  onSelect,
  onPreview,
}: CapitalStackScenarioCardsProps) {
  const { t } = useTranslation()
  const theme = useTheme()

  if (scenarios.length === 0) {
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
      {/* Header */}
      <Typography
        sx={{
          fontSize: 'var(--ob-font-size-sm)',
          fontWeight: 600,
          color: 'text.secondary',
          textTransform: 'uppercase',
          letterSpacing: 'var(--ob-letter-spacing-wider)',
          mb: 'var(--ob-space-050)',
        }}
      >
        {t('finance.capitalStack.selectScenario')}
      </Typography>

      {/* Scenario Cards */}
      {scenarios.map((scenario) => {
        const isActive = scenario.scenarioId === activeId
        return (
          <Box
            key={scenario.scenarioId}
            role="button"
            tabIndex={0}
            onClick={() => onSelect(scenario.scenarioId)}
            onKeyDown={(e: React.KeyboardEvent) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault()
                onSelect(scenario.scenarioId)
              }
            }}
            sx={{
              width: '100%',
              textAlign: 'left',
              p: 'var(--ob-space-100)',
              borderRadius: 'var(--ob-radius-sm)',
              border: 1,
              borderColor: isActive
                ? alpha(theme.palette.primary.main, 0.3)
                : 'divider',
              bgcolor: isActive
                ? alpha(theme.palette.primary.main, 0.05)
                : 'background.paper',
              boxShadow: isActive ? 1 : 0,
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              '&:hover': {
                borderColor: 'primary.main',
                boxShadow: 2,
              },
              '&:focus-visible': {
                outline: `2px solid ${theme.palette.primary.main}`,
                outlineOffset: 2,
              },
            }}
          >
            {/* Title Row */}
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                mb: 'var(--ob-space-025)',
              }}
            >
              <Typography
                sx={{
                  fontWeight: 700,
                  color: isActive ? 'primary.dark' : 'text.primary',
                  fontSize: 'var(--ob-font-size-md)',
                }}
              >
                {scenario.scenarioName}
              </Typography>
              {isActive && (
                <Box
                  sx={{
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    bgcolor: 'primary.main',
                    flexShrink: 0,
                  }}
                />
              )}
            </Box>

            {/* Description */}
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--ob-space-100)',
              }}
            >
              <Typography
                sx={{
                  fontSize: 'var(--ob-font-size-sm)',
                  color: isActive ? 'primary.main' : 'text.secondary',
                }}
              >
                {scenario.description || t('finance.capitalStack.baseCase')}
              </Typography>

              {/* Preview Button (only on active) */}
              {isActive && onPreview && (
                <Button
                  size="small"
                  variant="outlined"
                  onClick={(e) => {
                    e.stopPropagation()
                    onPreview(scenario)
                  }}
                  sx={{
                    borderRadius: 'var(--ob-radius-xs)',
                    fontSize: 'var(--ob-font-size-xs)',
                    py: 'var(--ob-space-025)',
                    px: 'var(--ob-space-075)',
                    ml: 'auto',
                  }}
                >
                  {t('finance.capitalStack.preview')}
                </Button>
              )}
            </Box>
          </Box>
        )
      })}
    </Box>
  )
}

export default CapitalStackScenarioCards
