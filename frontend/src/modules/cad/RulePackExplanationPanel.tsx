import { useMemo } from 'react'
import { Box, Typography, Stack, Grid, Skeleton } from '@mui/material'

import { useTranslation } from '../../i18n'
import type { RuleSummary } from '../../api/client'
import { GlassCard } from '../../components/canonical/GlassCard'
import { StatusChip } from '../../components/canonical/StatusChip'

interface RulePackExplanationPanelProps {
  rules: RuleSummary[]
  loading?: boolean
  /** When 'embedded', removes outer card surface for use inside a parent .ob-card-module */
  variant?: 'standalone' | 'embedded'
}

// Authority descriptions for context
const AUTHORITY_INFO: Record<string, { name: string; description: string }> = {
  BCA: {
    name: 'BCA',
    description:
      'Building & Construction Authority: Safety, Fire, & Accessibility',
  },
  URA: {
    name: 'URA',
    description: 'Urban Redevelopment Authority: Land Use, Height & Density',
  },
  NEA: {
    name: 'NEA',
    description:
      'National Environment Agency: Environmental & Waste Management',
  },
  LTA: {
    name: 'LTA',
    description: 'Land Transport Authority: Transport & Parking Requirements',
  },
  SCDF: {
    name: 'SCDF',
    description:
      'Singapore Civil Defence Force: Fire Safety & Emergency Access',
  },
}

// Rule descriptions based on parameterKey patterns
// Keys match the end portion of the full parameter_key (e.g., "zoning.max_far" → "max_far")
const RULE_DESCRIPTIONS: Record<
  string,
  { label: string; description: string; critical?: boolean }
> = {
  // Zoning rules
  max_far: {
    label: 'Plot Ratio',
    description: 'Intensity of development defined by Gross Floor Area.',
    critical: true,
  },
  max_fsi: {
    label: 'Floor Space Index',
    description: 'Ratio of total floor area to site area.',
    critical: true,
  },
  site_coverage: {
    label: 'Site Coverage',
    description: 'Total building footprint relative to site area.',
    critical: true,
  },
  max_percent: {
    label: 'Site Coverage',
    description: 'Maximum percentage of site that can be built upon.',
    critical: true,
  },
  max_building_height_m: {
    label: 'Maximum Height',
    description: 'Storey height limit for the specific zoning.',
  },
  max_building_height_ft: {
    label: 'Maximum Height',
    description: 'Storey height limit for the specific zoning.',
  },
  max_storeys: {
    label: 'Maximum Storeys',
    description: 'Number of floors limit for the building.',
  },
  // Setback rules
  front_min_m: {
    label: 'Setback (Road)',
    description: 'Minimum distance from building to road boundary.',
    critical: true,
  },
  side_min_m: {
    label: 'Setback (Side)',
    description: 'Minimum distance from building to side boundary.',
  },
  rear_min_m: {
    label: 'Setback (Rear)',
    description: 'Minimum distance from building to rear boundary.',
  },
  // Fire safety rules
  fire_access: {
    label: 'Fire Safety Access',
    description: 'Minimum width for fire engine access ways.',
    critical: true,
  },
  road_width_m: {
    label: 'Fire Safety Access',
    description: 'Minimum width for fire engine access ways.',
    critical: true,
  },
  max_travel_distance_m: {
    label: 'Fire Travel Distance',
    description: 'Maximum distance to emergency exit.',
    critical: true,
  },
  max_travel_distance_ft: {
    label: 'Fire Travel Distance',
    description: 'Maximum distance to emergency exit (ft).',
    critical: true,
  },
  // Accessibility rules
  ramp_gradient: {
    label: 'Ramp Gradient',
    description: 'Accessibility slope for wheelchair users.',
  },
  max_slope_ratio: {
    label: 'Ramp Gradient',
    description: 'Accessibility slope for wheelchair users.',
  },
  accessible_route_width_in: {
    label: 'Accessible Route Width',
    description: 'Minimum width for accessible routes.',
  },
  barrier_free_path_width_mm: {
    label: 'Barrier-Free Path',
    description: 'Minimum width for barrier-free access.',
  },
  // Ventilation rules
  ventilation_rate: {
    label: 'Ventilation Rate',
    description: 'Natural ventilation area per habitable room.',
  },
  natural_ventilation: {
    label: 'Ventilation Rate',
    description: 'Natural ventilation area per habitable room.',
  },
  // Communal/amenity rules
  communal_space: {
    label: 'Communal Space',
    description: 'Required shared landscaping or amenity space.',
  },
  open_space: {
    label: 'Communal Space',
    description: 'Required shared landscaping or amenity space.',
  },
  min_percent: {
    label: 'Communal Space',
    description: 'Required shared landscaping or amenity space.',
  },
  // Parking rules
  min_car_spaces_per_unit: {
    label: 'Parking Provision',
    description: 'Standard parking lots required per unit.',
    critical: true,
  },
  max_ramp_slope_ratio: {
    label: 'Ramp Gradient',
    description: 'Maximum slope ratio for parking ramps.',
  },
  bicycle_spaces_per_unit: {
    label: 'Bicycle Parking',
    description: 'Bicycle spaces required per unit.',
  },
}

// Humanize a parameter key to a readable label (fallback)
function humanizeParameterKey(parameterKey: string): string {
  return parameterKey
    .replace(/\./g, ' ')
    .replace(/_/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .split(' ')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

// Get rule info with fallback - matches by last segment of parameter_key
function getRuleInfo(parameterKey: string | undefined | null): {
  label: string
  description: string
  critical?: boolean
} {
  if (!parameterKey) {
    // Fallback for empty parameterKey - will still show the rule value
    return { label: '', description: '' }
  }

  // Try to match by the last segment(s) of the parameter key
  // e.g., "zoning.site_coverage.max_percent" → try "max_percent", then "site_coverage.max_percent"
  const segments = parameterKey.toLowerCase().split('.')

  // Try last segment first
  const lastSegment = segments[segments.length - 1]
  if (RULE_DESCRIPTIONS[lastSegment]) {
    return RULE_DESCRIPTIONS[lastSegment]
  }

  // Try last two segments combined
  if (segments.length >= 2) {
    const lastTwo = segments.slice(-2).join('_')
    if (RULE_DESCRIPTIONS[lastTwo]) {
      return RULE_DESCRIPTIONS[lastTwo]
    }
  }

  // Fallback: humanize the parameter key itself
  return {
    label: humanizeParameterKey(parameterKey),
    description: '',
  }
}

export function RulePackExplanationPanel({
  rules,
  loading = false,
  variant = 'standalone',
}: RulePackExplanationPanelProps) {
  const { t } = useTranslation()

  const isEmbedded = variant === 'embedded'

  const grouped = useMemo(
    () =>
      rules.reduce<Record<string, RuleSummary[]>>((acc, rule) => {
        const key = rule.authority || rule.topic || 'General'
        acc[key] = [...(acc[key] ?? []), rule]
        return acc
      }, {}),
    [rules],
  )

  const keys = useMemo(() => Object.keys(grouped).sort(), [grouped])

  // Loading state
  if (loading) {
    if (isEmbedded) {
      return (
        <Box sx={{ width: '100%' }}>
          <Typography variant="h6" sx={{ mb: 'var(--ob-space-200)' }}>
            {t('panels.rulePackTitle', { defaultValue: 'Rule constraints' })}
          </Typography>
          <Stack sx={{ gap: 'var(--ob-space-200)' }}>
            <Skeleton variant="rectangular" height={40} />
            <Skeleton variant="rectangular" height={40} />
            <Skeleton variant="rectangular" height={40} />
          </Stack>
        </Box>
      )
    }
    return (
      <GlassCard sx={{ p: 'var(--ob-space-300)' }}>
        <Typography variant="h6" sx={{ mb: 'var(--ob-space-300)' }}>
          {t('panels.rulePackTitle', { defaultValue: 'Rule constraints' })}
        </Typography>
        <Stack sx={{ gap: 'var(--ob-space-200)' }}>
          <Skeleton variant="rectangular" height={40} />
          <Skeleton variant="rectangular" height={40} />
          <Skeleton variant="rectangular" height={40} />
        </Stack>
      </GlassCard>
    )
  }

  // Empty state
  if (keys.length === 0) {
    if (isEmbedded) {
      return (
        <Typography variant="body2" color="text.secondary">
          {t('panels.rulePackEmpty', {
            defaultValue:
              'Rules will appear after the first overlays are processed.',
          })}
        </Typography>
      )
    }
    return (
      <GlassCard sx={{ p: 'var(--ob-space-300)', textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          {t('panels.rulePackEmpty', {
            defaultValue: 'No active rules for this selection.',
          })}
        </Typography>
      </GlassCard>
    )
  }

  // Content with rules - AI Studio "Content vs Context" pattern:
  // - Section header on background (context)
  // - Authority headers on background (context)
  // - Only data tables in cards (content)
  const RulesContent = (
    <>
      {/* Section header on background - CONTEXT (no card) */}
      <Typography
        variant="h6"
        fontWeight={600}
        sx={{ mb: 'var(--ob-space-050)' }}
      >
        {t('panels.rulePackTitle', { defaultValue: 'Rule pack explanation' })}
      </Typography>
      <Typography
        variant="body2"
        sx={{ color: 'var(--ob-text-secondary)', mb: 'var(--ob-space-300)' }}
      >
        Regulatory constraints from governing authorities
      </Typography>

      <Grid container spacing="var(--ob-space-300)">
        {keys.map((key) => {
          const authorityInfo = AUTHORITY_INFO[key] ?? {
            name: key,
            description: '',
          }
          return (
            <Grid item xs={12} md={6} key={key}>
              {/* Authority Header on BACKGROUND - CONTEXT (no card) */}
              <Box sx={{ mb: 'var(--ob-space-150)' }}>
                <Stack
                  direction="row"
                  sx={{
                    alignItems: 'center',
                    gap: 'var(--ob-space-100)',
                    mb: 'var(--ob-space-050)',
                  }}
                >
                  <Box
                    sx={{
                      width: 'var(--ob-size-indicator-dot)',
                      height: 'var(--ob-size-indicator-dot)',
                      borderRadius: '50%',
                      bgcolor: 'var(--ob-color-neon-cyan)',
                      flexShrink: 0,
                    }}
                  />
                  <Typography
                    variant="h6"
                    fontWeight={700}
                    sx={{ color: 'var(--ob-text-primary)' }}
                  >
                    {authorityInfo.name}
                  </Typography>
                </Stack>
                {authorityInfo.description && (
                  <Typography
                    variant="body2"
                    sx={{
                      color: 'var(--ob-text-secondary)',
                      pl: 'calc(var(--ob-size-indicator-dot) + var(--ob-space-100))',
                    }}
                  >
                    {authorityInfo.description}
                  </Typography>
                )}
              </Box>

              {/* Rules Table in CARD - CONTENT (actionable data) */}
              <Box
                className="ob-card-module"
                sx={{
                  borderRadius: 'var(--ob-radius-sm)',
                  overflow: 'hidden',
                }}
              >
                {/* Table Header */}
                <Stack
                  direction="row"
                  sx={{
                    px: 'var(--ob-space-200)',
                    py: 'var(--ob-space-150)',
                    borderBottom: '1px solid var(--ob-color-border-subtle)',
                  }}
                >
                  <Typography
                    variant="caption"
                    fontWeight={600}
                    sx={{
                      color: 'var(--ob-text-tertiary)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.1em',
                      flex: 1,
                    }}
                  >
                    Rule Identity
                  </Typography>
                  <Typography
                    variant="caption"
                    fontWeight={600}
                    sx={{
                      color: 'var(--ob-text-tertiary)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.1em',
                      textAlign: 'right',
                      minWidth: 'var(--ob-size-column-min)',
                    }}
                  >
                    Parameter
                  </Typography>
                </Stack>

                {/* Rules Rows */}
                <Stack sx={{ gap: '0' }}>
                  {grouped[key].map((rule, index) => {
                    const ruleInfo = getRuleInfo(rule.parameterKey)
                    // Build the rule value string (e.g., "<= 40%")
                    const ruleValue = `${rule.operator} ${rule.value}${rule.unit ? rule.unit : ''}`
                    // Use ruleInfo.label if available, otherwise humanize the key
                    const displayLabel =
                      ruleInfo.label ||
                      humanizeParameterKey(rule.parameterKey || 'Unknown')
                    return (
                      <Stack
                        key={rule.id}
                        direction="row"
                        sx={{
                          px: 'var(--ob-space-200)',
                          py: 'var(--ob-space-150)',
                          alignItems: 'flex-start',
                          borderBottom:
                            index < grouped[key].length - 1
                              ? '1px solid var(--ob-color-border-subtle)'
                              : 'none',
                        }}
                      >
                        {/* Left: Rule Identity */}
                        <Box sx={{ flex: 1, pr: 'var(--ob-space-200)' }}>
                          <Stack
                            direction="row"
                            sx={{
                              alignItems: 'center',
                              gap: 'var(--ob-space-100)',
                              mb: 'var(--ob-space-025)',
                              flexWrap: 'wrap',
                            }}
                          >
                            <Typography
                              variant="subtitle2"
                              fontWeight={600}
                              sx={{
                                color: ruleInfo.critical
                                  ? 'warning.main'
                                  : 'var(--ob-text-primary)',
                              }}
                            >
                              {displayLabel}
                            </Typography>
                            {ruleInfo.critical && (
                              <StatusChip status="warning" size="sm">
                                CRITICAL
                              </StatusChip>
                            )}
                          </Stack>
                          {ruleInfo.description && (
                            <Typography
                              variant="body2"
                              sx={{ color: 'var(--ob-text-secondary)' }}
                            >
                              {ruleInfo.description}
                            </Typography>
                          )}
                        </Box>

                        {/* Right: Parameter Value Pill */}
                        <Box
                          sx={{
                            px: 'var(--ob-space-150)',
                            py: 'var(--ob-space-050)',
                            borderRadius: 'var(--ob-radius-full)',
                            border: '1px solid var(--ob-color-border-subtle)',
                            bgcolor: 'var(--ob-surface-glass-1)',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          <Typography
                            variant="body2"
                            fontWeight={500}
                            sx={{
                              color: ruleInfo.critical
                                ? 'warning.main'
                                : 'var(--ob-text-primary)',
                            }}
                          >
                            {ruleValue}
                          </Typography>
                        </Box>
                      </Stack>
                    )
                  })}
                </Stack>
              </Box>
            </Grid>
          )
        })}
      </Grid>
    </>
  )

  // Embedded variant: no outer card, full width
  if (isEmbedded) {
    return <Box sx={{ width: '100%' }}>{RulesContent}</Box>
  }

  // Standalone variant: original with GlassCard
  return (
    <GlassCard
      sx={{
        p: 'var(--ob-space-300)',
        maxWidth: 1000,
        width: '100%',
        mx: 'auto',
      }}
    >
      {RulesContent}
    </GlassCard>
  )
}

export default RulePackExplanationPanel
