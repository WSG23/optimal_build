/**
 * ConceptPreviewSection - 3D preview viewer and starter model status card
 *
 * Extracted from DeveloperResults to reduce file size.
 */

import { Suspense, lazy } from 'react'
import { Box, Typography, Select, MenuItem, FormControl } from '@mui/material'
import RefreshIcon from '@mui/icons-material/Refresh'
import ViewInArIcon from '@mui/icons-material/ViewInAr'

import type { DevelopmentScenario } from '../../../../api/agents'
import { Card } from '../../../../components/canonical/Card'
import { Button } from '../../../../components/canonical/Button'

import type { CaptureResultV2StarterModel } from './useStarterModelMemos'
import type { PreviewFallbackMassingInput } from '../../../components/site-acquisition/previewFallbackMassing'

const Preview3DViewer = lazy(async () => {
  const module =
    await import('../../../components/site-acquisition/Preview3DViewer')
  return { default: module.Preview3DViewer }
})

export interface ConceptPreviewSectionProps {
  effectiveStarterModel: CaptureResultV2StarterModel
  previewDetailLevel: 'simple' | 'medium'
  setPreviewDetailLevel: (level: 'simple' | 'medium') => void
  isGeneratingStarterModel: boolean
  isRefreshingPreview: boolean
  starterModelActionLabel: string
  starterModelStatusSummary: string
  handleEnsureStarterModel: () => Promise<void>
  formatScenarioLabel: (
    scenario: DevelopmentScenario | 'all' | null | undefined,
  ) => string
  recommendedScenario: DevelopmentScenario
  supportsFullCompliance: boolean
  previewMetadataError: string | null
  previewGenerationError: string | null
  fallbackMassing: PreviewFallbackMassingInput | null
}

export function ConceptPreviewSection({
  effectiveStarterModel,
  previewDetailLevel,
  setPreviewDetailLevel,
  isGeneratingStarterModel,
  isRefreshingPreview,
  starterModelActionLabel,
  starterModelStatusSummary,
  handleEnsureStarterModel,
  formatScenarioLabel,
  recommendedScenario,
  supportsFullCompliance,
  previewMetadataError,
  previewGenerationError,
  fallbackMassing,
}: ConceptPreviewSectionProps) {
  return (
    <section className="site-acquisition__preview">
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
          Concept Preview
        </Typography>
        <Box
          sx={{
            display: 'flex',
            gap: 'var(--ob-space-100)',
            alignItems: 'center',
          }}
        >
          <FormControl size="small">
            <Select
              value={previewDetailLevel}
              onChange={(e) =>
                setPreviewDetailLevel(e.target.value as 'simple' | 'medium')
              }
              disabled={isGeneratingStarterModel || isRefreshingPreview}
              sx={{ minWidth: 'var(--ob-size-600)' }}
            >
              <MenuItem value="simple">Simple</MenuItem>
              <MenuItem value="medium">Medium</MenuItem>
            </Select>
          </FormControl>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => void handleEnsureStarterModel()}
            disabled={isRefreshingPreview || isGeneratingStarterModel}
          >
            <RefreshIcon
              sx={{
                fontSize: 'var(--ob-font-size-md)',
                mr: 'var(--ob-space-025)',
              }}
            />
            {starterModelActionLabel}
          </Button>
        </Box>
      </Box>

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', lg: '2fr 1fr' },
          gap: 'var(--ob-space-150)',
        }}
      >
        {/* 3D Viewer */}
        <Suspense
          fallback={
            <Card
              sx={{
                minHeight: 420,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                p: 'var(--ob-space-150)',
              }}
            >
              <Typography
                sx={{
                  fontSize: 'var(--ob-font-size-sm)',
                  color: 'text.secondary',
                }}
              >
                Loading 3D preview...
              </Typography>
            </Card>
          }
        >
          <Preview3DViewer
            previewUrl={effectiveStarterModel.modelUrl}
            metadataUrl={effectiveStarterModel.metadataUrl}
            status={effectiveStarterModel.status}
            thumbnailUrl={effectiveStarterModel.thumbnailUrl}
            fallbackMassing={fallbackMassing}
          />
        </Suspense>

        <Card
          sx={{
            p: 'var(--ob-space-125)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--ob-space-075)',
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
              Starter Model Status
            </Typography>
          </Box>
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-lg)',
              fontWeight: 'var(--ob-font-weight-bold)',
              color: 'text.primary',
              textTransform: 'capitalize',
            }}
          >
            {effectiveStarterModel.status.replace(/_/g, ' ')}
            {isGeneratingStarterModel ? ' (updating)' : ''}
          </Typography>
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-sm)',
              color: 'text.secondary',
              lineHeight: 'var(--ob-line-height-normal)',
            }}
          >
            {starterModelStatusSummary}
          </Typography>
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-sm)',
              color: 'text.secondary',
              lineHeight: 'var(--ob-line-height-normal)',
            }}
          >
            Geometry scope:{' '}
            {effectiveStarterModel.geometryScope.replace(/_/g, ' ')}.
            {effectiveStarterModel.floorsEstimate != null
              ? ` Estimated floors: ${effectiveStarterModel.floorsEstimate}.`
              : ' Floor count estimate pending.'}
          </Typography>
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-xs)',
              color: 'text.secondary',
            }}
          >
            Starter model scenario: {formatScenarioLabel(recommendedScenario)}
          </Typography>
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-xs)',
              color: 'text.secondary',
            }}
          >
            Full compliance support: {supportsFullCompliance ? 'Yes' : 'No'}
          </Typography>
        </Card>
      </Box>

      {previewMetadataError && (
        <Typography color="error" sx={{ mt: 'var(--ob-space-050)' }}>
          {previewMetadataError}
        </Typography>
      )}
      {previewGenerationError && (
        <Typography color="error" sx={{ mt: 'var(--ob-space-050)' }}>
          {previewGenerationError}
        </Typography>
      )}
    </section>
  )
}
