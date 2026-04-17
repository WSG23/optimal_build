/**
 * Concept Preview Section
 *
 * 3D preview viewer with controls for detail level, refresh, and layer management.
 * Extracted from SiteAcquisitionPage for component size management.
 */

import {
  Box,
  Stack,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material'
import Refresh from '@mui/icons-material/Refresh'
import { Button } from '../../../../components/canonical/Button'
import { Preview3DViewer } from '../../../components/site-acquisition/Preview3DViewer'
import type { GeometryDetailLevel } from '../../../../api/siteAcquisition'
import { PREVIEW_DETAIL_OPTIONS, PREVIEW_DETAIL_LABELS } from '../constants'
import { describeDetailLevel } from '../utils'
import { PreviewLayersTable, type LayerAction } from './property-overview'

interface ConceptPreviewSectionProps {
  previewJob: {
    previewUrl: string
    status: string
    thumbnailUrl?: string
    geometryDetailLevel: GeometryDetailLevel
  }
  previewViewerMetadataUrl: string | null
  previewDetailLevel: GeometryDetailLevel
  setPreviewDetailLevel: (level: GeometryDetailLevel) => void
  isRefreshingPreview: boolean
  handleRefreshPreview: () => void
  previewLayerVisibility: Record<string, boolean>
  previewFocusLayerId: string | null
  previewLayerMetadata: Array<{
    layerId: string
    name: string
    [key: string]: unknown
  }>
  hiddenLayerCount: number
  isPreviewMetadataLoading: boolean
  previewMetadataError: string | null
  onLayerAction: (layerId: string, action: LayerAction) => void
  onShowAllLayers: () => void
  onResetLayerFocus: () => void
  formatNumberMetric: (
    value: number,
    options?: Intl.NumberFormatOptions,
  ) => string
  colorLegendEntries: Array<{
    id: string
    label: string
    color: string
  }>
  onLegendChange: (id: string, color: string) => void
  legendHasPendingChanges: boolean
  onLegendReset: () => void
}

export function ConceptPreviewSection({
  previewJob,
  previewViewerMetadataUrl,
  previewDetailLevel,
  setPreviewDetailLevel,
  isRefreshingPreview,
  handleRefreshPreview,
  previewLayerVisibility,
  previewFocusLayerId,
  previewLayerMetadata,
  hiddenLayerCount,
  isPreviewMetadataLoading,
  previewMetadataError,
  onLayerAction,
  onShowAllLayers,
  onResetLayerFocus,
  formatNumberMetric,
  colorLegendEntries,
  onLegendChange,
  legendHasPendingChanges,
  onLegendReset,
}: ConceptPreviewSectionProps) {
  return (
    <>
      <Box
        sx={{
          mt: 'var(--ob-space-400)',
          bgcolor: 'background.default',
          borderRadius: 'var(--ob-radius-sm)',
          overflow: 'hidden',
        }}
      >
        {/* Header */}
        <Box
          sx={{
            p: 'var(--ob-space-200)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderBottom: '1px solid',
            borderColor: 'divider',
          }}
        >
          <Typography variant="h6">Concept Preview</Typography>
          <Typography
            variant="overline"
            sx={{
              px: 'var(--ob-space-100)',
              border: '1px solid',
              borderColor: 'secondary.main',
              borderRadius: 'var(--ob-radius-xs)',
            }}
          >
            {previewJob.status.toUpperCase()}
          </Typography>
        </Box>

        {/* Preview surface */}
        <Box sx={{ display: 'block' }}>
          <Box
            sx={{
              minHeight: 'var(--ob-size-controls-min)',
              bgcolor: 'var(--ob-color-bg-root)',
              borderRadius: 'var(--ob-radius-sm)',
              overflow: 'hidden',
            }}
          >
            <Preview3DViewer
              previewUrl={previewJob.previewUrl}
              metadataUrl={previewViewerMetadataUrl}
              status={previewJob.status}
              thumbnailUrl={previewJob.thumbnailUrl}
              layerVisibility={previewLayerVisibility}
              focusLayerId={previewFocusLayerId}
            />
          </Box>
        </Box>

        {/* Controls bar */}
        <Box
          sx={{
            p: 'var(--ob-space-200)',
            borderTop: '1px solid',
            borderColor: 'divider',
          }}
        >
          <Stack
            direction="row"
            spacing="var(--ob-space-300)"
            alignItems="center"
          >
            <FormControl
              size="small"
              sx={{ minWidth: 'var(--ob-size-input-sm)' }}
            >
              <InputLabel>Preview Detail</InputLabel>
              <Select
                value={previewDetailLevel}
                label="Preview Detail"
                onChange={(e) => {
                  setPreviewDetailLevel(e.target.value as GeometryDetailLevel)
                }}
                disabled={isRefreshingPreview || !previewJob}
              >
                {PREVIEW_DETAIL_OPTIONS.map((option) => (
                  <MenuItem key={option} value={option}>
                    {PREVIEW_DETAIL_LABELS[option]}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Button
              variant="secondary"
              size="sm"
              onClick={handleRefreshPreview}
              disabled={isRefreshingPreview || !previewJob}
            >
              <Refresh
                className={isRefreshingPreview ? 'fa-spin' : ''}
                sx={{
                  fontSize: 'var(--ob-font-size-base)',
                  mr: 'var(--ob-space-050)',
                }}
              />
              {isRefreshingPreview ? 'Refreshing...' : 'Refresh Preview Status'}
            </Button>

            <Typography variant="caption" color="text.secondary">
              Preview detail:{' '}
              <strong>
                {describeDetailLevel(previewJob.geometryDetailLevel)}
              </strong>
            </Typography>
          </Stack>
        </Box>
      </Box>

      {/* Master Table */}
      <PreviewLayersTable
        layers={previewLayerMetadata}
        visibility={previewLayerVisibility}
        focusLayerId={previewFocusLayerId}
        hiddenLayerCount={hiddenLayerCount}
        isLoading={isPreviewMetadataLoading}
        error={previewMetadataError}
        onLayerAction={onLayerAction}
        onShowAll={onShowAllLayers}
        onResetFocus={onResetLayerFocus}
        formatNumber={formatNumberMetric}
        legendEntries={colorLegendEntries}
        onLegendChange={onLegendChange}
        legendHasPendingChanges={legendHasPendingChanges}
        onLegendReset={onLegendReset}
      />
    </>
  )
}
