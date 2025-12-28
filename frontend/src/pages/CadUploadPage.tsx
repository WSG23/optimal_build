import { useCallback, useEffect, useId, useRef, useState } from 'react'
import { Box, Stack, MenuItem, Typography } from '@mui/material'

import {
  type CadImportSummary,
  type ParseStatusUpdate,
  useApiClient,
} from '../api/client'
import { AppLayout } from '../App'
import { useTranslation } from '../i18n'
import CadUploader from '../modules/cad/CadUploader'
import RulePackExplanationPanel from '../modules/cad/RulePackExplanationPanel'
import useRules from '../hooks/useRules'
import { Input } from '../components/canonical/Input'

const DEFAULT_PROJECT_ID = 1
const DEFAULT_ZONE_CODE = 'SG:residential'

const ZONE_OPTIONS: Array<{ value: string; labelKey: string }> = [
  { value: 'SG:residential', labelKey: 'residential' },
  { value: 'SG:commercial', labelKey: 'commercial' },
  { value: 'SG:industrial', labelKey: 'industrial' },
  { value: 'SG:mixed_use', labelKey: 'mixedUse' },
  { value: 'SG:business_park', labelKey: 'businessPark' },
]

export function CadUploadPage() {
  const apiClient = useApiClient()
  const { t } = useTranslation()
  const [job, setJob] = useState<CadImportSummary | null>(null)
  const [status, setStatus] = useState<ParseStatusUpdate | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [projectId, setProjectId] = useState<number>(DEFAULT_PROJECT_ID)
  const [zoneCode, setZoneCode] = useState<string>(DEFAULT_ZONE_CODE)
  const cancelRef = useRef<(() => void) | null>(null)
  const { rules, loading } = useRules(apiClient)
  const projectIdInputId = useId()
  const zoneInputId = useId()

  useEffect(() => {
    return () => {
      cancelRef.current?.()
    }
  }, [])

  const handleUpload = useCallback(
    async (file: File) => {
      cancelRef.current?.()
      setIsUploading(true)
      setError(null)
      try {
        const summary = await apiClient.uploadCadDrawing(file, {
          projectId,
          zoneCode,
        })
        setJob(summary)
        setStatus({
          importId: summary.importId,
          status: summary.parseStatus,
          requestedAt: null,
          completedAt: null,
          jobId: null,
          detectedFloors: summary.detectedFloors,
          detectedUnits: summary.detectedUnits,
          metadata: summary.vectorSummary ?? null,
          error: null,
        })
        const initial = await apiClient.triggerParse(summary.importId)
        setStatus(initial)
        cancelRef.current = apiClient.pollParseStatus({
          importId: summary.importId,
          onUpdate: (update) => {
            setStatus(update)
          },
          intervalMs: 2500,
        })
      } catch (err) {
        console.error('CAD Upload Failed:', err)
        const msg =
          err instanceof Error ? err.message : t('common.errors.uploadFailed')
        setError(msg)
      } finally {
        setIsUploading(false)
      }
    },
    [apiClient, projectId, t, zoneCode],
  )

  const Controls = (
    <Stack
      direction="row"
      spacing="var(--ob-space-200)"
      sx={{ minWidth: 'var(--ob-size-controls-min)' }}
    >
      <Input
        id={projectIdInputId}
        label={t('uploader.projectLabel')}
        type="number"
        value={projectId}
        onChange={(event) => {
          const value = Number(event.target.value)
          if (Number.isNaN(value) || value <= 0) {
            setProjectId(DEFAULT_PROJECT_ID)
            return
          }
          setProjectId(Math.trunc(value))
        }}
        size="small"
        sx={{ flex: 1 }}
      />
      <Input
        id={zoneInputId}
        select
        label={t('uploader.zoneLabel')}
        value={zoneCode}
        onChange={(event) => {
          setZoneCode(event.target.value)
        }}
        size="small"
        sx={{ flex: 1.5 }}
      >
        {ZONE_OPTIONS.map((option) => (
          <MenuItem key={option.value} value={option.value}>
            {t(`uploader.zoneOptions.${option.labelKey}`)}
          </MenuItem>
        ))}
      </Input>
    </Stack>
  )

  return (
    <AppLayout title={t('uploader.title')} subtitle={t('uploader.subtitle')}>
      <Box className="cad-upload" sx={{ pb: 'var(--ob-space-800)' }}>
        <Stack spacing="var(--ob-space-300)">
          {/* Context Bar - Depth 1 (Glass Card with cyan edge) */}
          <Box
            className="ob-card-module"
            sx={{
              p: 'var(--ob-space-200)',
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--ob-space-100)',
            }}
          >
            <Typography
              variant="subtitle2"
              sx={{
                color: 'text.secondary',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                mr: 'var(--ob-space-200)',
              }}
            >
              Project Settings
            </Typography>
            {Controls}
          </Box>

          {/* Error Banner */}
          {error && (
            <Box
              sx={{
                p: 'var(--ob-space-200)',
                border: '1px solid var(--ob-error-500)',
                borderRadius: 'var(--ob-radius-sm)',
                bgcolor: 'var(--ob-error-muted)',
                color: 'var(--ob-error-icon)',
              }}
            >
              {error}
            </Box>
          )}

          {/* CAD Uploader - Depth 1 (Glass Card with cyan edge) */}
          <Box className="ob-card-module">
            <CadUploader
              onUpload={(file) => {
                void handleUpload(file)
              }}
              isUploading={isUploading}
              status={status}
              summary={job}
            />
          </Box>

          {/* Rules Panel - Depth 1 (Glass Card with cyan edge) */}
          <Box className="ob-card-module">
            <RulePackExplanationPanel rules={rules} loading={loading} />
          </Box>
        </Stack>
      </Box>
    </AppLayout>
  )
}

export default CadUploadPage
