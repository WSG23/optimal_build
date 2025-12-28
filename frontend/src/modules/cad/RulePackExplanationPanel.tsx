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
            defaultValue: 'Rules will appear after the first overlays are processed.',
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

  // Content with rules
  const RulesContent = (
    <>
      <Typography
        variant="h6"
        fontWeight={600}
        gutterBottom
        sx={{ mb: 'var(--ob-space-200)' }}
      >
        {t('panels.rulePackTitle', { defaultValue: 'Rule constraints' })}
      </Typography>

      <Grid container spacing={3}>
        {keys.map((key) => (
          <Grid item xs={12} md={6} key={key}>
            <Box
              sx={{
                borderRadius: 'var(--ob-radius-sm)',
                border: '1px solid var(--ob-color-border-subtle)',
                overflow: 'hidden',
              }}
            >
              <Box
                sx={{
                  p: 'var(--ob-space-200)',
                  bgcolor: 'var(--ob-surface-glass-2)',
                  borderBottom: '1px solid var(--ob-color-border-subtle)',
                }}
              >
                <Typography
                  variant="subtitle2"
                  fontWeight={600}
                  sx={{
                    color: 'var(--ob-brand-500)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    m: 0,
                  }}
                >
                  {key}
                </Typography>
              </Box>
              <Stack
                sx={{
                  p: 0,
                  bgcolor: 'var(--ob-surface-glass-1)',
                }}
              >
                {grouped[key].map((rule, index) => (
                  <Box
                    key={rule.id}
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      py: 'var(--ob-space-100)',
                      px: 'var(--ob-space-150)',
                      minHeight: 48,
                      borderBottom:
                        index < grouped[key].length - 1
                          ? '1px solid var(--ob-color-border-subtle)'
                          : 'none',
                      '&:hover': {
                        bgcolor: 'action.hover',
                      },
                    }}
                  >
                    <Typography
                      variant="body2"
                      sx={{
                        color: 'var(--ob-text-primary)',
                        fontSize: '0.875rem',
                      }}
                    >
                      {rule.parameterKey}
                    </Typography>
                    <Stack
                      direction="row"
                      sx={{ gap: 'var(--ob-space-100)', alignItems: 'center' }}
                    >
                      <StatusChip status="neutral" size="sm">
                        {`${rule.operator} ${rule.value}${rule.unit || ''}`}
                      </StatusChip>
                      {rule.overlays.length > 0 && (
                        <StatusChip status="info" size="sm">
                          {rule.overlays.join(', ')}
                        </StatusChip>
                      )}
                    </Stack>
                  </Box>
                ))}
              </Stack>
            </Box>
          </Grid>
        ))}
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
