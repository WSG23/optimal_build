import { Box, Divider, Grid, Stack, Typography } from '@mui/material'
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Area,
  AreaChart,
} from 'recharts'

import { AppLayout } from '../../App'
import { useTranslation } from '../../i18n'

import { TimelinePanel } from './components'
import { useDeals, useTimeline, useAnalytics, useBenchmarks } from './hooks'
import { STAGE_TRANSLATION_KEYS } from './types'
import {
  formatCurrency,
  formatDays,
  formatPercent,
  formatShortCurrency,
} from './utils/formatters'
import { AnimatedPageHeader } from '../../components/canonical/AnimatedPageHeader'
import { MetricTile } from '../../components/canonical/MetricTile'
import { Card } from '../../components/canonical/Card'
import { AttachMoney, TrendingUp, Speed, Assignment } from '@mui/icons-material'

export default function AgentPerformancePage() {
  const { t, i18n } = useTranslation()
  const locale = i18n.language

  const {
    loadingDeals: _loadingDeals,
    dealError: _dealError,
    selectedDealId,
    selectedDeal,
    groupedDeals,
    stageOrder,
    setSelectedDealId,
  } = useDeals({ t })

  const {
    timeline,
    timelineLoading,
    timelineError: _timelineError,
  } = useTimeline({
    selectedDealId,
    t,
  })

  const selectedAgentId = selectedDeal?.agentId ?? null
  const primaryCurrency = selectedDeal?.estimatedValueCurrency ?? 'SGD'

  const { latestSnapshot, analyticsLoading, analyticsError, trendData } =
    useAnalytics({
      selectedAgentId,
      locale,
      t,
    })

  const fallbackText = t('agentPerformance.common.fallback')

  const {
    benchmarksLoading: _benchmarksLoading,
    benchmarksError: _benchmarksError,
    benchmarkComparisons: _benchmarkComparisons,
    benchmarksHasContent,
  } = useBenchmarks({
    selectedDeal,
    latestSnapshot,
    locale,
    fallbackText,
    t,
  })

  const loadingText = t('common.loading')

  const analyticsHasContent =
    Boolean(latestSnapshot) ||
    trendData.length > 0 ||
    analyticsLoading ||
    analyticsError ||
    benchmarksHasContent

  return (
    <AppLayout
      title={t('agentPerformance.title')}
      subtitle={t('agentPerformance.subtitle')}
    >
      <Box sx={{ p: 3 }}>
        <AnimatedPageHeader
          title={t('agentPerformance.title')}
          subtitle={t('agentPerformance.subtitle')}
          breadcrumbs={[
            { label: 'Dashboard', href: '/' },
            { label: 'Agent Performance' },
          ]}
        />

        <Grid container spacing={3}>
          {/* Kanban Section */}
          <Grid item xs={12} lg={8}>
            <Card variant="glass" sx={{ p: 2, height: '100%', minHeight: 400 }}>
              <Stack
                direction="row"
                spacing={2}
                sx={{ overflowX: 'auto', pb: 2 }}
              >
                {stageOrder.map((stage) => {
                  const items = groupedDeals[stage] ?? []
                  const label =
                    t(STAGE_TRANSLATION_KEYS[stage]) ??
                    STAGE_TRANSLATION_KEYS[stage]

                  return (
                    <Box key={stage} sx={{ minWidth: 280, flexShrink: 0 }}>
                      <Box
                        sx={{
                          pb: 1,
                          borderBottom: 2,
                          borderColor: 'divider',
                          mb: 2,
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                        }}
                      >
                        <Typography
                          variant="subtitle2"
                          sx={{ fontWeight: 600 }}
                        >
                          {label}
                        </Typography>
                        <Typography
                          variant="caption"
                          sx={{
                            background: 'rgba(0,0,0,0.05)',
                            px: 1,
                            borderRadius: '2px', // Square Cyber-Minimalism: xs for badges
                          }}
                        >
                          {items.length}
                        </Typography>
                      </Box>

                      <Stack spacing={1}>
                        {items.map((deal) => (
                          <Card
                            variant="glass"
                            key={deal.id}
                            hover="lift"
                            sx={{
                              p: 1.5,
                              cursor: 'pointer',
                              border:
                                selectedDealId === deal.id
                                  ? '1px solid var(--ob-color-brand-primary)'
                                  : undefined,
                              background:
                                selectedDealId === deal.id
                                  ? 'var(--ob-color-brand-soft)'
                                  : undefined,
                            }}
                            onClick={() => setSelectedDealId(deal.id)}
                          >
                            <Typography variant="subtitle2">
                              {deal.title}
                            </Typography>
                            <Typography
                              variant="caption"
                              display="block"
                              color="text.secondary"
                            >
                              {deal.estimatedValueCurrency}{' '}
                              {deal.estimatedValueAmount !== null
                                ? deal.estimatedValueAmount.toLocaleString(
                                    locale,
                                  )
                                : '-'}
                            </Typography>
                          </Card>
                        ))}
                      </Stack>
                    </Box>
                  )
                })}
              </Stack>
            </Card>
          </Grid>

          {/* Timeline Sidebar */}
          <Grid item xs={12} lg={4}>
            <TimelinePanel
              events={timeline}
              loading={timelineLoading}
              locale={locale}
              fallbackText={fallbackText}
              loadingText={loadingText}
              auditLabel={t('agentPerformance.timeline.auditLabel')}
              durationLabel={t('agentPerformance.timeline.durationLabel')}
              changedByLabel={t('agentPerformance.timeline.changedBy')}
              noteLabel={t('agentPerformance.timeline.note')}
              hashLabel={t('agentPerformance.timeline.hash')}
              signatureLabel={t('agentPerformance.timeline.signature')}
              stageLabelFor={(stage) =>
                t(STAGE_TRANSLATION_KEYS[stage]) ?? stage
              }
            />
          </Grid>

          {/* Analytics Section */}
          {analyticsHasContent && (
            <Grid item xs={12}>
              <Divider sx={{ my: 4 }} />
              <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>
                {t('agentPerformance.analytics.title')}
              </Typography>

              <Grid container spacing={3} sx={{ mb: 4 }}>
                {latestSnapshot &&
                  [
                    {
                      label: t('agentPerformance.analytics.metrics.openDeals'),
                      value: latestSnapshot.dealsOpen.toLocaleString(locale),
                      icon: <Assignment />,
                    },
                    {
                      label: t(
                        'agentPerformance.analytics.metrics.grossPipelineValue',
                      ),
                      value: formatCurrency(
                        latestSnapshot.grossPipelineValue,
                        primaryCurrency,
                        locale,
                        fallbackText,
                      ),
                      icon: <AttachMoney />,
                      variant: 'primary' as const,
                    },
                    {
                      label: t(
                        'agentPerformance.analytics.metrics.conversionRate',
                      ),
                      value: formatPercent(
                        latestSnapshot.conversionRate,
                        fallbackText,
                      ),
                      icon: <TrendingUp />,
                    },
                    {
                      label: t(
                        'agentPerformance.analytics.metrics.avgCycleDays',
                      ),
                      value: formatDays(
                        latestSnapshot.avgCycleDays,
                        fallbackText,
                      ),
                      icon: <Speed />,
                    },
                  ].map((metric, idx) => (
                    <Grid item xs={12} sm={6} md={3} key={idx}>
                      <MetricTile
                        label={metric.label as string}
                        value={metric.value as string}
                        icon={metric.icon}
                        variant="default"
                      />
                    </Grid>
                  ))}
              </Grid>

              {trendData.length > 0 && (
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Card variant="glass" sx={{ p: 2, height: 320 }}>
                      <Typography variant="h6" gutterBottom>
                        {t('agentPerformance.analytics.trend.pipelineHeading')}
                      </Typography>
                      <ResponsiveContainer width="100%" height="90%">
                        <AreaChart data={trendData}>
                          <defs>
                            <linearGradient
                              id="colorGross"
                              x1="0"
                              y1="0"
                              x2="0"
                              y2="1"
                            >
                              <stop
                                offset="5%"
                                stopColor="#3B82F6"
                                stopOpacity={0.3}
                              />
                              <stop
                                offset="95%"
                                stopColor="#3B82F6"
                                stopOpacity={0}
                              />
                            </linearGradient>
                          </defs>
                          <CartesianGrid
                            strokeDasharray="3 3"
                            vertical={false}
                          />
                          <XAxis dataKey="label" tick={{ fontSize: 12 }} />
                          <YAxis
                            tick={{ fontSize: 12 }}
                            tickFormatter={(val) =>
                              formatShortCurrency(val, primaryCurrency, locale)
                            }
                          />
                          <Tooltip />
                          <Area
                            type="monotone"
                            dataKey="gross"
                            stroke="#3B82F6"
                            fillOpacity={1}
                            fill="url(#colorGross)"
                          />
                          <Area
                            type="monotone"
                            dataKey="weighted"
                            stroke="#10B981"
                            fillOpacity={0}
                            strokeDasharray="4 4"
                          />
                        </AreaChart>
                      </ResponsiveContainer>
                    </Card>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Card variant="glass" sx={{ p: 2, height: 320 }}>
                      <Typography variant="h6" gutterBottom>
                        {t(
                          'agentPerformance.analytics.trend.conversionHeading',
                        )}
                      </Typography>
                      <ResponsiveContainer width="100%" height="90%">
                        <LineChart data={trendData}>
                          <CartesianGrid
                            strokeDasharray="3 3"
                            vertical={false}
                          />
                          <XAxis dataKey="label" tick={{ fontSize: 12 }} />
                          <YAxis
                            tick={{ fontSize: 12 }}
                            tickFormatter={(val) => `${val}%`}
                          />
                          <Tooltip />
                          <Line
                            type="monotone"
                            dataKey="conversion"
                            stroke="#F59E0B"
                            strokeWidth={2}
                          />
                          <Line
                            type="monotone"
                            dataKey="cycle"
                            stroke="#8B5CF6"
                            strokeWidth={2}
                            strokeDasharray="4 4"
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </Card>
                  </Grid>
                </Grid>
              )}
            </Grid>
          )}
        </Grid>
      </Box>
    </AppLayout>
  )
}
