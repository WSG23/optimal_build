/**
 * CaptureRecommendationSection - Recommendation card and starter model assumptions card
 *
 * Extracted from DeveloperResults to reduce file size.
 */

import { useState } from 'react'
import { Box, Typography } from '@mui/material'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'
import ViewInArIcon from '@mui/icons-material/ViewInAr'

import type { DevelopmentScenario } from '../../../../api/agents'
import { Card } from '../../../../components/canonical/Card'
import { Button } from '../../../../components/canonical/Button'
import { Tag } from '../../../../components/canonical/Tag'

import type {
  CaptureDataBasisItem,
  StarterModelAssetProfileLine,
  StarterModelAssumptionLine,
  StarterModelAssumptionBuckets,
} from './useStarterModelMemos'

export interface CaptureRecommendationSectionProps {
  recommendationCardTitle: string
  formatScenarioLabel: (
    scenario: DevelopmentScenario | 'all' | null | undefined,
  ) => string
  recommendedScenario: DevelopmentScenario
  userOverride: boolean
  defaultRecommendationLabel: string
  explanation: string
  programDirectionLabel: string
  programDirectionSummary: string
  programDrivers: string[]
  overrideModeLine: string
  overrideIntentGuidance: string | null
  overrideIntent: string | null | undefined
  currentProject: { id: string; name: string } | null
  confidence: string
  scenarioFitSummary: {
    comparisonSummary: string
    headroomSummary: string
    heritageSummary: string
  }
  captureDataBasis: CaptureDataBasisItem[]
  reasonCodes: string[]
  handleSaveProjectOverride: () => void
  handleClearProjectOverride: () => void
  starterModelAssumptionSourceLine: string
  starterModelAssumptionFallbackReason: string | null
  starterModelOverridePreviewNotice: string | null
  starterModelAssumptionBuckets: StarterModelAssumptionBuckets
  starterModelAssumptionLines: StarterModelAssumptionLine[]
  starterModelAssetProfileLines: StarterModelAssetProfileLine[]
}

function formatReasonLabel(code: string): string {
  return code
    .replace(/^EXPLORATORY_OVERRIDE$/i, 'Exploratory override')
    .replace(/^SAVED_OVERRIDE$/i, 'Saved override')
    .replace(/^USER_OVERRIDE$/i, 'User override')
    .replace(/^HERITAGE_OVERLAY$/i, 'Heritage overlay')
    .replace(/^CONSERVATION_REVIEW_REQUIRED$/i, 'Conservation review')
    .replace(/^CURRENT_GFA_ABOVE_MAX$/i, 'Current bulk above code max')
    .replace(/^CURRENT_GFA_BELOW_MAX$/i, 'Current bulk below code max')
    .replace(/^CURRENT_GFA_AT_MAX$/i, 'Current bulk at code max')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

function labelValueRow(label: string, value: string) {
  return (
    <Box
      key={label}
      sx={{
        display: 'grid',
        gridTemplateColumns: { xs: '1fr', sm: '140px 1fr' },
        gap: 'var(--ob-space-050)',
        alignItems: 'start',
      }}
    >
      <Typography
        sx={{
          fontSize: 'var(--ob-font-size-xs)',
          fontWeight: 'var(--ob-font-weight-semibold)',
          color: 'text.secondary',
          textTransform: 'uppercase',
          letterSpacing: '0.04em',
        }}
      >
        {label}
      </Typography>
      <Typography
        sx={{
          fontSize: 'var(--ob-font-size-sm)',
          color: 'text.primary',
          lineHeight: 'var(--ob-line-height-normal)',
        }}
      >
        {value}
      </Typography>
    </Box>
  )
}

function buildProgramBasis(
  programDrivers: string[],
  recommendedScenario: DevelopmentScenario,
): string | null {
  const primary = programDrivers[0]
  if (!primary) {
    return null
  }

  const parts = [`${primary} primary`]
  const secondary = programDrivers.find((driver) => driver !== primary)
  if (secondary) {
    parts.push(`${secondary} support`)
  }

  if (recommendedScenario === 'heritage_property') {
    parts.push('Heritage constrained')
  }

  return parts.join(' / ')
}

function dataBasisItem(item: CaptureDataBasisItem) {
  return (
    <Box
      key={item.label}
      sx={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--ob-space-025)',
      }}
    >
      <Typography
        sx={{
          fontSize: 'var(--ob-font-size-xs)',
          fontWeight: 'var(--ob-font-weight-semibold)',
          color: 'text.secondary',
          textTransform: 'uppercase',
          letterSpacing: '0.04em',
        }}
      >
        {item.label}
      </Typography>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--ob-space-050)',
          flexWrap: 'wrap',
        }}
      >
        <Tag color={item.tone} size="sm">
          {item.statusLabel}
        </Tag>
        <Typography
          sx={{
            fontSize: 'var(--ob-font-size-xs)',
            color: 'text.secondary',
            lineHeight: 'var(--ob-line-height-normal)',
          }}
        >
          {item.value}
        </Typography>
      </Box>
    </Box>
  )
}

function compactStatusItem(item: CaptureDataBasisItem | undefined) {
  if (!item) {
    return null
  }

  return (
    <Box
      key={item.label}
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--ob-space-050)',
        flexWrap: 'wrap',
      }}
    >
      <Tag color={item.tone} size="sm">
        {item.statusLabel}
      </Tag>
      <Typography
        sx={{
          fontSize: 'var(--ob-font-size-xs)',
          color: 'text.secondary',
          lineHeight: 'var(--ob-line-height-normal)',
        }}
      >
        {item.value}
      </Typography>
    </Box>
  )
}

export function CaptureRecommendationSection({
  recommendationCardTitle,
  formatScenarioLabel,
  recommendedScenario,
  userOverride,
  defaultRecommendationLabel,
  explanation,
  programDirectionLabel,
  programDirectionSummary,
  programDrivers,
  overrideModeLine,
  overrideIntentGuidance,
  overrideIntent,
  currentProject,
  confidence,
  scenarioFitSummary,
  captureDataBasis,
  reasonCodes,
  handleSaveProjectOverride,
  handleClearProjectOverride,
  starterModelAssumptionSourceLine,
  starterModelAssumptionFallbackReason,
  starterModelOverridePreviewNotice,
  starterModelAssumptionBuckets,
  starterModelAssumptionLines,
  starterModelAssetProfileLines,
}: CaptureRecommendationSectionProps) {
  const [showDataDetails, setShowDataDetails] = useState(false)
  const programBasis = buildProgramBasis(programDrivers, recommendedScenario)
  const metadataRows = [
    ['Mode', overrideModeLine],
    ['Confidence', confidence.replace(/_/g, ' ')],
    ['Program direction', programDirectionLabel],
    ...(programBasis ? [['Program basis', programBasis]] : []),
    ['Code fit', scenarioFitSummary.comparisonSummary],
    ['GFA envelope', scenarioFitSummary.headroomSummary],
    [
      'Context',
      scenarioFitSummary.heritageSummary.replace(/^Context:\s*/i, ''),
    ],
  ]
  const captureCompleteness = captureDataBasis.find(
    (item) => item.label === 'Capture completeness',
  )
  const resolvedControls = captureDataBasis.find(
    (item) => item.label === 'Resolved controls',
  )
  const unresolvedControls = captureDataBasis.find(
    (item) => item.label === 'Official controls pending',
  )
  const sourceIngestion = captureDataBasis.find(
    (item) => item.label === 'Source ingestion status',
  )
  const liveSourceScan = captureDataBasis.find(
    (item) => item.label === 'Live source scan',
  )
  const hasSourceReview = Boolean(unresolvedControls) || Boolean(liveSourceScan)
  const hasDataDetails =
    captureDataBasis.length > 0 || programDrivers.length > 0
  const detailToggleLabel = showDataDetails
    ? 'Hide data details'
    : 'Show data details'

  return (
    <section className="site-acquisition__capture-summary">
      <Box
        sx={{
          mb: 'var(--ob-space-150)',
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', xl: '1fr 1fr' },
          gap: 'var(--ob-space-150)',
        }}
      >
        <Card
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
              flexDirection: 'column',
              gap: 'var(--ob-space-075)',
              pb: 'var(--ob-space-050)',
            }}
          >
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: 'var(--ob-space-075)',
                flexWrap: 'wrap',
              }}
            >
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--ob-space-050)',
                }}
              >
                <AutoAwesomeIcon
                  sx={{
                    fontSize: 'var(--ob-size-icon-sm)',
                    color: 'info.main',
                  }}
                />
                <Typography
                  sx={{
                    fontSize: 'var(--ob-font-size-xs)',
                    fontWeight: 'var(--ob-font-weight-semibold)',
                    letterSpacing: '0.05em',
                    textTransform: 'uppercase',
                    color: 'text.secondary',
                  }}
                >
                  {recommendationCardTitle}
                </Typography>
              </Box>
              <Tag color={userOverride ? 'warning' : 'info'} size="sm">
                {overrideModeLine}
              </Tag>
            </Box>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-lg)',
                fontWeight: 'var(--ob-font-weight-bold)',
                color: 'text.primary',
              }}
            >
              {formatScenarioLabel(recommendedScenario)}
            </Typography>
            {userOverride ? (
              <Typography
                sx={{
                  fontSize: 'var(--ob-font-size-xs)',
                  color: 'text.secondary',
                }}
              >
                Capture recommended: {defaultRecommendationLabel}
              </Typography>
            ) : null}
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-sm)',
                color: 'text.secondary',
                lineHeight: 'var(--ob-line-height-normal)',
              }}
            >
              {explanation}
            </Typography>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-sm)',
                color: 'text.secondary',
                lineHeight: 'var(--ob-line-height-normal)',
              }}
            >
              {programDirectionSummary}
            </Typography>
            {overrideIntentGuidance ? (
              <Typography
                sx={{
                  fontSize: 'var(--ob-font-size-xs)',
                  color: 'text.secondary',
                  lineHeight: 'var(--ob-line-height-normal)',
                }}
              >
                {overrideIntentGuidance}
              </Typography>
            ) : null}
          </Box>

          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--ob-space-075)',
              mt: 'var(--ob-space-025)',
              pt: 'var(--ob-space-100)',
              borderTop: 'var(--ob-border-fine)',
            }}
          >
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-xs)',
                fontWeight: 'var(--ob-font-weight-semibold)',
                color: 'text.secondary',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
              }}
            >
              Decision Brief
            </Typography>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--ob-space-050)',
                flexWrap: 'wrap',
              }}
            >
              <Tag color={userOverride ? 'warning' : 'info'} size="sm">
                {overrideModeLine}
              </Tag>
              <Tag color="success" size="sm">
                {confidence.replace(/_/g, ' ')} confidence
              </Tag>
              {captureCompleteness ? (
                <Tag color={captureCompleteness.tone} size="sm">
                  {captureCompleteness.statusLabel}
                </Tag>
              ) : null}
            </Box>
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' },
                gap: 'var(--ob-space-075) var(--ob-space-125)',
              }}
            >
              {labelValueRow('Program', programDirectionLabel)}
              {programBasis ? labelValueRow('Use basis', programBasis) : null}
              {labelValueRow('Code fit', scenarioFitSummary.comparisonSummary)}
              {labelValueRow(
                'GFA envelope',
                scenarioFitSummary.headroomSummary,
              )}
            </Box>
            {resolvedControls ? compactStatusItem(resolvedControls) : null}
            {hasSourceReview ? (
              <Box
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 'var(--ob-space-050)',
                  p: 'var(--ob-space-075)',
                  border: '1px solid rgba(234, 179, 8, 0.2)',
                  borderRadius: 'var(--ob-radius-xs)',
                  background: 'rgba(234, 179, 8, 0.04)',
                }}
              >
                <Typography
                  sx={{
                    fontSize: 'var(--ob-font-size-xs)',
                    fontWeight: 'var(--ob-font-weight-semibold)',
                    color: 'warning.main',
                    textTransform: 'uppercase',
                    letterSpacing: '0.04em',
                  }}
                >
                  Official controls pending
                </Typography>
                {unresolvedControls
                  ? compactStatusItem(unresolvedControls)
                  : null}
                {liveSourceScan ? compactStatusItem(liveSourceScan) : null}
              </Box>
            ) : null}
          </Box>

          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--ob-space-050)',
            }}
          >
            {hasDataDetails ? (
              <Box
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 'var(--ob-space-075)',
                }}
              >
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: 'var(--ob-space-075)',
                    flexWrap: 'wrap',
                  }}
                >
                  <Typography
                    sx={{
                      fontSize: 'var(--ob-font-size-xs)',
                      fontWeight: 'var(--ob-font-weight-semibold)',
                      color: 'text.secondary',
                      textTransform: 'uppercase',
                      letterSpacing: '0.04em',
                    }}
                  >
                    Audit Trail
                  </Typography>
                  <Button
                    variant="ghost"
                    size="sm"
                    aria-expanded={showDataDetails}
                    aria-controls="capture-data-basis-details"
                    onClick={() => setShowDataDetails((current) => !current)}
                  >
                    {detailToggleLabel}
                  </Button>
                </Box>
                {showDataDetails && hasDataDetails ? (
                  <Box
                    id="capture-data-basis-details"
                    sx={{
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 'var(--ob-space-075)',
                      pt: 'var(--ob-space-075)',
                      borderTop: 'var(--ob-border-fine)',
                    }}
                  >
                    <Box
                      sx={{
                        display: 'grid',
                        gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
                        gap: 'var(--ob-space-075) var(--ob-space-125)',
                      }}
                    >
                      {metadataRows.map(([label, value]) =>
                        labelValueRow(label, value),
                      )}
                    </Box>
                    {captureDataBasis.length > 0 ? (
                      <Box
                        sx={{
                          display: 'grid',
                          gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
                          gap: 'var(--ob-space-050) var(--ob-space-100)',
                        }}
                      >
                        {captureDataBasis.map((item) => dataBasisItem(item))}
                      </Box>
                    ) : null}
                    {programDrivers.length > 0 ? (
                      <Box
                        sx={{
                          display: 'flex',
                          flexDirection: 'column',
                          gap: 'var(--ob-space-050)',
                        }}
                      >
                        <Typography
                          sx={{
                            fontSize: 'var(--ob-font-size-xs)',
                            fontWeight: 'var(--ob-font-weight-semibold)',
                            color: 'text.secondary',
                            textTransform: 'uppercase',
                            letterSpacing: '0.04em',
                          }}
                        >
                          Use Signals
                        </Typography>
                        <Box
                          sx={{
                            display: 'flex',
                            flexWrap: 'wrap',
                            gap: 'var(--ob-space-050)',
                          }}
                        >
                          {programDrivers.map((driver) => (
                            <Tag key={driver} color="default" size="sm">
                              {driver}
                            </Tag>
                          ))}
                        </Box>
                      </Box>
                    ) : null}
                  </Box>
                ) : null}
              </Box>
            ) : null}
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-xs)',
                fontWeight: 'var(--ob-font-weight-semibold)',
                color: 'text.secondary',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
              }}
            >
              Decision Drivers
            </Typography>
            <Box
              sx={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: 'var(--ob-space-050)',
              }}
            >
              {reasonCodes.map((code) => (
                <Tag
                  key={code}
                  color={
                    code.includes('HERITAGE') || code.includes('CONSERVATION')
                      ? 'warning'
                      : code.includes('OVERRIDE')
                        ? 'info'
                        : 'default'
                  }
                  size="sm"
                >
                  {formatReasonLabel(code)}
                </Tag>
              ))}
            </Box>
          </Box>

          <Box
            sx={{
              display: 'flex',
              gap: 'var(--ob-space-050)',
              flexWrap: 'wrap',
            }}
          >
            {overrideIntent === 'exploratory' && currentProject ? (
              <Button
                variant="secondary"
                size="sm"
                onClick={handleSaveProjectOverride}
              >
                Save as Project Override
              </Button>
            ) : null}
            {overrideIntent === 'saved' && currentProject ? (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClearProjectOverride}
              >
                Clear Saved Override
              </Button>
            ) : null}
          </Box>
        </Card>

        <Card
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
              alignItems: 'center',
              gap: 'var(--ob-space-050)',
            }}
          >
            <ViewInArIcon
              sx={{
                fontSize: 'var(--ob-size-icon-sm)',
                color: 'info.main',
              }}
            />
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-xs)',
                fontWeight: 'var(--ob-font-weight-semibold)',
                letterSpacing: '0.05em',
                textTransform: 'uppercase',
                color: 'text.secondary',
              }}
            >
              Starter Model Assumptions
            </Typography>
          </Box>
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-sm)',
              color: 'text.secondary',
              lineHeight: 'var(--ob-line-height-normal)',
            }}
          >
            These defaults shape the first scenario-specific model before deeper
            engineering inputs are added.
          </Typography>
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-xs)',
              color: 'text.secondary',
              lineHeight: 'var(--ob-line-height-normal)',
            }}
          >
            These values are modeling assumptions, not certified code controls.
          </Typography>
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-xs)',
              color: 'text.secondary',
              lineHeight: 'var(--ob-line-height-normal)',
            }}
          >
            {starterModelAssumptionSourceLine}
          </Typography>
          {starterModelAssumptionFallbackReason ? (
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-xs)',
                color: 'text.secondary',
                lineHeight: 'var(--ob-line-height-normal)',
              }}
            >
              {starterModelAssumptionFallbackReason}
            </Typography>
          ) : null}
          {starterModelOverridePreviewNotice ? (
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-xs)',
                color: 'text.secondary',
                lineHeight: 'var(--ob-line-height-normal)',
              }}
            >
              {starterModelOverridePreviewNotice}
            </Typography>
          ) : null}

          {starterModelAssumptionBuckets.pinned.length > 0 ||
          starterModelAssumptionBuckets.tunable.length > 0 ? (
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' },
                gap: 'var(--ob-space-075)',
              }}
            >
              {starterModelAssumptionBuckets.pinned.length > 0 ? (
                <Box
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 'var(--ob-space-050)',
                  }}
                >
                  <Typography
                    sx={{
                      fontSize: 'var(--ob-font-size-xs)',
                      fontWeight: 'var(--ob-font-weight-semibold)',
                      color: 'text.secondary',
                      textTransform: 'uppercase',
                      letterSpacing: '0.04em',
                    }}
                  >
                    Pinned by site facts
                  </Typography>
                  <Box
                    sx={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: 'var(--ob-space-050)',
                    }}
                  >
                    {starterModelAssumptionBuckets.pinned.map((item) => (
                      <Tag key={item} color="warning" size="sm">
                        {item}
                      </Tag>
                    ))}
                  </Box>
                </Box>
              ) : null}
              {starterModelAssumptionBuckets.tunable.length > 0 ? (
                <Box
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 'var(--ob-space-050)',
                  }}
                >
                  <Typography
                    sx={{
                      fontSize: 'var(--ob-font-size-xs)',
                      fontWeight: 'var(--ob-font-weight-semibold)',
                      color: 'text.secondary',
                      textTransform: 'uppercase',
                      letterSpacing: '0.04em',
                    }}
                  >
                    Model inputs open for refinement
                  </Typography>
                  <Box
                    sx={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: 'var(--ob-space-050)',
                    }}
                  >
                    {starterModelAssumptionBuckets.tunable.map((item) => (
                      <Tag key={item} color="default" size="sm">
                        {item}
                      </Tag>
                    ))}
                  </Box>
                </Box>
              ) : null}
            </Box>
          ) : null}

          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--ob-space-075)',
              pt: 'var(--ob-space-050)',
              borderTop: 'var(--ob-border-fine)',
            }}
          >
            {starterModelAssumptionLines.map((line) => (
              <Box
                key={line.label}
                sx={{
                  display: 'grid',
                  gridTemplateColumns: { xs: '1fr', md: '160px 1fr auto' },
                  gap: 'var(--ob-space-050)',
                  alignItems: 'center',
                }}
              >
                <Typography
                  sx={{
                    fontSize: 'var(--ob-font-size-xs)',
                    fontWeight: 'var(--ob-font-weight-semibold)',
                    color: 'text.secondary',
                    textTransform: 'uppercase',
                    letterSpacing: '0.04em',
                  }}
                >
                  {line.label}
                </Typography>
                <Typography
                  sx={{
                    fontSize: 'var(--ob-font-size-sm)',
                    color: 'text.primary',
                    lineHeight: 'var(--ob-line-height-normal)',
                  }}
                >
                  {line.value}
                </Typography>
                {line.sourceDetail ? (
                  <Box sx={{ justifySelf: 'start' }}>
                    <Tag color="info" size="sm">
                      {line.sourceDetail}
                    </Tag>
                  </Box>
                ) : null}
              </Box>
            ))}
          </Box>

          {starterModelAssetProfileLines.length > 0 ? (
            <Box
              sx={{
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--ob-space-075)',
                pt: 'var(--ob-space-050)',
                borderTop: 'var(--ob-border-fine)',
              }}
            >
              <Typography
                sx={{
                  fontSize: 'var(--ob-font-size-xs)',
                  fontWeight: 'var(--ob-font-weight-semibold)',
                  color: 'text.secondary',
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                }}
              >
                Use-Type Profiles
              </Typography>
              {starterModelAssetProfileLines.map((line) => (
                <Box
                  key={line.label}
                  sx={{
                    display: 'grid',
                    gridTemplateColumns: { xs: '1fr', md: '160px 1fr auto' },
                    gap: 'var(--ob-space-050)',
                    alignItems: 'center',
                  }}
                >
                  <Typography
                    sx={{
                      fontSize: 'var(--ob-font-size-xs)',
                      fontWeight: 'var(--ob-font-weight-semibold)',
                      color: 'text.secondary',
                      textTransform: 'uppercase',
                      letterSpacing: '0.04em',
                    }}
                  >
                    {line.label}
                  </Typography>
                  <Typography
                    sx={{
                      fontSize: 'var(--ob-font-size-sm)',
                      color: 'text.primary',
                      lineHeight: 'var(--ob-line-height-normal)',
                    }}
                  >
                    {line.value}
                  </Typography>
                  {line.sourceDetail ? (
                    <Box sx={{ justifySelf: 'start' }}>
                      <Tag color="info" size="sm">
                        {line.sourceDetail}
                      </Tag>
                    </Box>
                  ) : null}
                </Box>
              ))}
            </Box>
          ) : null}
        </Card>
      </Box>
    </section>
  )
}
