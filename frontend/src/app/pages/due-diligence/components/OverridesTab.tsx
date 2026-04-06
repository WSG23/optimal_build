import { Box, Typography } from '@mui/material'

import type {
  ConditionAssessment,
  DevelopmentScenario,
  SiteAcquisitionResult,
} from '../../../../api/siteAcquisition'
import { Button } from '../../../../components/canonical/Button'
import type { ScenarioComparisonDatum } from '../../site-acquisition/types'

type ScenarioOverrideEntry = ConditionAssessment & {
  scenario: DevelopmentScenario
}

export interface OverridesTabProps {
  capturedProperty: SiteAcquisitionResult
  isExportingReport: boolean
  reportExportMessage: string | null
  handleReportExport: (format: 'json' | 'pdf') => void
  scenarioOverrideEntries: ScenarioOverrideEntry[]
  baseScenarioAssessment: ConditionAssessment | null
  scenarioComparisonEntries: ConditionAssessment[]
  scenarioComparisonTableRows: ScenarioComparisonDatum[]
  isLoadingScenarioAssessments: boolean
  scenarioAssessmentsError: string | null
  setScenarioComparisonBase: (scenario: DevelopmentScenario) => void
  formatScenarioLabel: (
    scenario: DevelopmentScenario | 'all' | null | undefined,
  ) => string
  formatRecordedTimestamp: (timestamp?: string | null) => string
}

function getAverageCondition(rows: ScenarioComparisonDatum[]): string {
  const scores = rows
    .map((row) => row.conditionScore)
    .filter((value): value is number => typeof value === 'number')
  if (scores.length === 0) {
    return 'Pending'
  }
  const average =
    scores.reduce((total, value) => total + value, 0) / scores.length
  return `${average.toFixed(0)}/100`
}

function getRiskVector(rows: ScenarioComparisonDatum[]): string {
  const elevated = rows.filter((row) =>
    String(row.riskLevel ?? '')
      .toLowerCase()
      .match(/high|critical|elevated/),
  ).length
  if (elevated === 0) {
    return 'Stable'
  }
  if (elevated === 1) {
    return '1 elevated path'
  }
  return `${elevated} elevated paths`
}

function getGaugeLabel(rows: ScenarioComparisonDatum[]): string {
  if (rows.length === 0) {
    return 'No scenario data'
  }
  const completed = rows.filter(
    (row) => (row.checklistPercent ?? 0) >= 50,
  ).length
  return `${completed}/${rows.length} scenarios advancing`
}

export function OverridesTab({
  capturedProperty,
  isExportingReport,
  reportExportMessage,
  handleReportExport,
  scenarioOverrideEntries,
  baseScenarioAssessment,
  scenarioComparisonEntries,
  scenarioComparisonTableRows,
  isLoadingScenarioAssessments,
  scenarioAssessmentsError,
  setScenarioComparisonBase,
  formatScenarioLabel,
  formatRecordedTimestamp,
}: OverridesTabProps) {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--ob-space-150)',
      }}
    >
      <Box
        className="ob-seamless-panel ob-seamless-panel--glass"
        sx={{
          p: 'var(--ob-space-150)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--ob-space-125)',
        }}
      >
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            gap: 'var(--ob-space-100)',
            flexWrap: 'wrap',
          }}
        >
          <Box>
            <Typography variant="h5" sx={{ m: 0, fontWeight: 600 }}>
              Due Diligence Matrix
            </Typography>
            <Typography
              color="text.secondary"
              sx={{ mt: 'var(--ob-space-025)' }}
            >
              Compare override outcomes across recorded development paths for{' '}
              {capturedProperty.address?.fullAddress ??
                capturedProperty.propertyInfo?.propertyName ??
                'the active property'}
              .
            </Typography>
          </Box>
          <Box
            sx={{
              display: 'flex',
              gap: 'var(--ob-space-075)',
              flexWrap: 'wrap',
            }}
          >
            <Button
              variant="primary"
              size="sm"
              onClick={() => handleReportExport('json')}
              disabled={isExportingReport}
            >
              {isExportingReport ? 'Exporting…' : 'Export JSON'}
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => handleReportExport('pdf')}
              disabled={isExportingReport}
            >
              {isExportingReport ? 'Exporting…' : 'Export PDF'}
            </Button>
          </Box>
        </Box>

        <Box
          sx={{
            display: 'grid',
            gap: 'var(--ob-space-100)',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          }}
        >
          {[
            ['DILIGENCE GAUGE', getGaugeLabel(scenarioComparisonTableRows)],
            ['RISK_VECTOR', getRiskVector(scenarioComparisonTableRows)],
            ['AVG_CONDITION', getAverageCondition(scenarioComparisonTableRows)],
            [
              'AVG_CONDITION',
              `${scenarioComparisonEntries.length} comparison paths`,
            ],
          ].map(([label, value]) => (
            <Box
              key={`${label}-${value}`}
              className="ob-seamless-panel"
              sx={{ p: 'var(--ob-space-100)' }}
            >
              <Typography
                sx={{
                  fontSize: 'var(--ob-font-size-2xs)',
                  letterSpacing: '0.08em',
                  textTransform: 'uppercase',
                  color: 'text.secondary',
                }}
              >
                {label}
              </Typography>
              <Typography
                variant="h6"
                sx={{ m: 0, mt: 'var(--ob-space-050)', fontWeight: 600 }}
              >
                {value}
              </Typography>
            </Box>
          ))}
        </Box>

        {reportExportMessage ? (
          <Typography color="text.secondary">{reportExportMessage}</Typography>
        ) : null}
      </Box>

      {scenarioOverrideEntries.length > 1 ? (
        <Box
          className="ob-seamless-panel ob-seamless-panel--glass"
          sx={{ p: 'var(--ob-space-125)' }}
        >
          <Typography variant="h6" sx={{ m: 0, fontWeight: 600 }}>
            Baseline scenario
          </Typography>
          <Box
            sx={{
              display: 'flex',
              gap: 'var(--ob-space-075)',
              flexWrap: 'wrap',
              mt: 'var(--ob-space-100)',
            }}
          >
            {scenarioOverrideEntries.map((entry) => {
              const isActive =
                baseScenarioAssessment?.scenario != null &&
                baseScenarioAssessment.scenario === entry.scenario
              return (
                <Button
                  key={entry.scenario}
                  variant={isActive ? 'primary' : 'secondary'}
                  size="sm"
                  onClick={() => setScenarioComparisonBase(entry.scenario)}
                >
                  {formatScenarioLabel(entry.scenario)}
                </Button>
              )
            })}
          </Box>
        </Box>
      ) : null}

      {scenarioAssessmentsError ? (
        <Box
          className="ob-seamless-panel ob-seamless-panel--glass"
          sx={{ p: 'var(--ob-space-150)' }}
        >
          <Typography color="error.main">{scenarioAssessmentsError}</Typography>
        </Box>
      ) : isLoadingScenarioAssessments ? (
        <Box
          className="ob-seamless-panel ob-seamless-panel--glass"
          sx={{ p: 'var(--ob-space-150)' }}
        >
          <Typography color="text.secondary">
            Loading scenario override matrix...
          </Typography>
        </Box>
      ) : scenarioComparisonTableRows.length === 0 ? (
        <Box
          className="ob-seamless-panel ob-seamless-panel--glass"
          sx={{ p: 'var(--ob-space-150)' }}
        >
          <Typography color="text.secondary">
            Save a scenario-specific inspection to compare diligence outcomes.
          </Typography>
        </Box>
      ) : (
        <Box
          sx={{
            display: 'grid',
            gap: 'var(--ob-space-125)',
            gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          }}
        >
          {scenarioComparisonTableRows.map((row) => (
            <Box
              key={row.key}
              className="ob-seamless-panel ob-seamless-panel--glass"
              sx={{
                p: 'var(--ob-space-125)',
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--ob-space-100)',
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
                <Box>
                  <Typography variant="h6" sx={{ m: 0, fontWeight: 600 }}>
                    {row.label || formatScenarioLabel(row.key)}
                  </Typography>
                  <Typography
                    color="text.secondary"
                    sx={{ mt: 'var(--ob-space-025)' }}
                  >
                    {row.quickHeadline ?? 'Assessment captured for this path.'}
                  </Typography>
                </Box>
                <Typography
                  sx={{
                    fontSize: 'var(--ob-font-size-2xs)',
                    letterSpacing: '0.08em',
                    textTransform: 'uppercase',
                    color: 'text.secondary',
                  }}
                >
                  {row.icon}
                </Typography>
              </Box>

              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
                  gap: 'var(--ob-space-075)',
                }}
              >
                <Box>
                  <Typography
                    sx={{
                      fontSize: 'var(--ob-font-size-2xs)',
                      color: 'text.secondary',
                    }}
                  >
                    Condition
                  </Typography>
                  <Typography sx={{ fontWeight: 600 }}>
                    {row.conditionRating ?? 'Pending'}
                    {row.conditionScore != null
                      ? ` · ${row.conditionScore}/100`
                      : ''}
                  </Typography>
                </Box>
                <Box>
                  <Typography
                    sx={{
                      fontSize: 'var(--ob-font-size-2xs)',
                      color: 'text.secondary',
                    }}
                  >
                    Checklist
                  </Typography>
                  <Typography sx={{ fontWeight: 600 }}>
                    {row.checklistCompleted ?? 0}/{row.checklistTotal ?? 0}
                  </Typography>
                </Box>
                <Box>
                  <Typography
                    sx={{
                      fontSize: 'var(--ob-font-size-2xs)',
                      color: 'text.secondary',
                    }}
                  >
                    Risk
                  </Typography>
                  <Typography sx={{ fontWeight: 600 }}>
                    {row.riskLevel ?? 'Pending'}
                  </Typography>
                </Box>
                <Box>
                  <Typography
                    sx={{
                      fontSize: 'var(--ob-font-size-2xs)',
                      color: 'text.secondary',
                    }}
                  >
                    Logged
                  </Typography>
                  <Typography sx={{ fontWeight: 600 }}>
                    {formatRecordedTimestamp(row.recordedAt)}
                  </Typography>
                </Box>
              </Box>

              {row.primaryInsight ? (
                <Box
                  className="ob-seamless-panel"
                  sx={{ p: 'var(--ob-space-100)' }}
                >
                  <Typography sx={{ fontWeight: 600 }}>
                    {row.primaryInsight.title}
                  </Typography>
                  <Typography
                    color="text.secondary"
                    sx={{ mt: 'var(--ob-space-025)' }}
                  >
                    {row.primaryInsight.detail}
                  </Typography>
                </Box>
              ) : null}
            </Box>
          ))}
        </Box>
      )}
    </Box>
  )
}
