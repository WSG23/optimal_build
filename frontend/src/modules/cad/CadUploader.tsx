import { ChangeEvent, DragEvent, useRef, useState } from 'react'
import {
  Box,
  Typography,
  Stack,
  Stepper,
  Step,
  StepLabel,
  Skeleton,
  Grid,
  Divider,
} from '@mui/material'
import {
  CloudUpload,
  Error as ErrorIcon,
  InsertDriveFile,
} from '@mui/icons-material'

import type { CadImportSummary, ParseStatusUpdate } from '../../api/client'
import { useTranslation } from '../../i18n'
import { GlassCard } from '../../components/canonical/GlassCard'
import { StatusChip } from '../../components/canonical/StatusChip'

interface CadUploaderProps {
  onUpload: (file: File) => void
  isUploading?: boolean
  status?: ParseStatusUpdate | null
  summary?: CadImportSummary | null
}

export function CadUploader({
  onUpload,
  isUploading = false,
  status,
  summary,
}: CadUploaderProps) {
  const { t } = useTranslation()
  const inputRef = useRef<HTMLInputElement | null>(null)
  const [isDragging, setIsDragging] = useState(false)

  const handleFiles = (files: FileList | null) => {
    if (!files || files.length === 0) return
    onUpload(files[0])
  }

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsDragging(false)
    handleFiles(event.dataTransfer.files)
  }

  const handleDragOver = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsDragging(false)
  }

  const handleBrowse = () => {
    inputRef.current?.click()
  }

  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    handleFiles(event.target.files)
  }

  // Determine active step for Stepper
  const getActiveStep = () => {
    if (status?.status === 'completed') return 3
    if (status?.status === 'failed') return 1
    if (
      isUploading ||
      status?.status === 'pending' ||
      status?.status === 'queued'
    )
      return 0
    if (status?.status === 'running') return 1
    return -1
  }
  const activeStep = getActiveStep()

  const detectedFloors = status?.detectedFloors ?? summary?.detectedFloors ?? []
  const detectedUnits = status?.detectedUnits ?? summary?.detectedUnits ?? []

  const steps = [
    t('uploader.steps.uploading', 'Uploading'),
    t('uploader.steps.processing', 'Processing Layers'),
    t('uploader.steps.detecting', 'Detecting Units'),
  ]

  return (
    <Box className="cad-uploader" sx={{ maxWidth: 1400, margin: '0 auto' }}>
      <Grid container spacing={3}>
        {/* Left Col: Hero Drop Zone */}
        <Grid item xs={12} lg={8}>
          <GlassCard
            className="cad-drop-zone"
            onClick={!isUploading ? handleBrowse : undefined}
            onDrop={!isUploading ? handleDrop : undefined}
            onDragOver={!isUploading ? handleDragOver : undefined}
            onDragLeave={!isUploading ? handleDragLeave : undefined}
            sx={{
              height: 280, // Reduced from 400px for better proportion
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: '2px dashed',
              borderColor: isDragging
                ? 'var(--ob-brand-500)'
                : 'var(--ob-color-border-subtle)',
              backgroundColor: isDragging ? 'var(--ob-brand-50)' : undefined,
              cursor: isUploading ? 'default' : 'pointer',
              transition: 'all 0.2s ease',
              '&:hover': {
                borderColor: !isUploading ? 'var(--ob-brand-500)' : undefined,
                backgroundColor: !isUploading
                  ? 'var(--ob-brand-50)'
                  : undefined,
              },
            }}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".dxf,.ifc,.json,.pdf,.svg,.jpg,.jpeg,.png"
              style={{ display: 'none' }}
              onChange={handleChange}
              disabled={isUploading}
            />
            <Stack
              sx={{
                gap: 'var(--ob-space-200)',
                alignItems: 'center',
                textAlign: 'center',
              }}
            >
              <Box
                sx={{
                  width: 64, // Reduced from 80
                  height: 64,
                  borderRadius: '50%',
                  backgroundColor: 'var(--ob-brand-100)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--ob-brand-500)',
                }}
              >
                {isUploading ? (
                  <Box
                    className="dot-flashing"
                    sx={{ transform: 'scale(1.2)' }}
                  />
                ) : (
                  <CloudUpload sx={{ fontSize: 32 }} />
                )}
              </Box>
              <Box>
                <Typography variant="h6" fontWeight={600} gutterBottom>
                  {isUploading
                    ? t('uploader.uploadingTitle', 'Uploading & Processing...')
                    : t('uploader.dropTitle', 'Upload CAD File')}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {isUploading
                    ? t(
                        'uploader.uploadingHint',
                        'Please wait while we analyze your file.',
                      )
                    : t('uploader.dropHint', 'Drag & drop or click to browse')}
                </Typography>
              </Box>
              {!isUploading && (
                <Typography variant="caption" color="text.disabled">
                  {t(
                    'uploader.supportedFormats',
                    'Supports .dxf, .ifc, .pdf, .png',
                  )}
                </Typography>
              )}
            </Stack>
          </GlassCard>
        </Grid>

        {/* Right Col: Status & Explanation */}
        <Grid item xs={12} lg={4}>
          <Stack sx={{ height: '100%', gap: 'var(--ob-space-300)' }}>
            {/* Stepper Status */}
            <GlassCard
              sx={{
                p: 'var(--ob-space-300)',
                flex: 1,
                maxHeight: 280,
                overflow: 'auto',
              }}
            >
              <Typography
                variant="subtitle1"
                fontWeight={600}
                gutterBottom
                sx={{ mb: 'var(--ob-space-200)' }}
              >
                {t('uploader.latestStatus', 'Processing Status')}
              </Typography>

              <Stepper activeStep={activeStep} orientation="vertical">
                {steps.map((label) => (
                  <Step key={label}>
                    <StepLabel
                      StepIconProps={{
                        sx: {
                          width: 20,
                          height: 20,
                          '&.Mui-active': { color: 'var(--ob-brand-500)' },
                          '&.Mui-completed': {
                            color: 'var(--ob-success-500)',
                          },
                        },
                      }}
                      sx={{
                        '& .MuiStepLabel-label': { fontSize: '0.875rem' },
                      }}
                    >
                      {label}
                    </StepLabel>
                  </Step>
                ))}
              </Stepper>

              {status?.error && (
                <Box
                  sx={{
                    mt: 'var(--ob-space-200)',
                    p: 'var(--ob-space-150)',
                    borderRadius: 'var(--ob-radius-sm)',
                    backgroundColor: 'var(--ob-error-muted)',
                    color: 'var(--ob-error-600)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--ob-space-150)',
                  }}
                >
                  <ErrorIcon fontSize="small" />
                  <Typography variant="caption" sx={{ lineHeight: 1.2 }}>
                    {status.error}
                  </Typography>
                </Box>
              )}
            </GlassCard>

            {/* Stats removed from here? No, let's keep it but maybe below or merged if we want compactness.
                Wait, previous implementation had "Meta Data" separate.
                If I reduce height to 280, grid item matching height might mean the status card is also 280.
                Splitting into two cards (Status + Meta) in the right col might be tight for 280px total?
                Let's combine them or putting the Meta data BELOW the dropzones in a full width?
                No, horizontal split is better.
                Let's keep the Meta Data card but make it compact.
            */}
            <GlassCard sx={{ p: 'var(--ob-space-200)' }}>
              <Stack sx={{ gap: 'var(--ob-space-150)' }}>
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <Stack
                    direction="row"
                    sx={{ gap: 'var(--ob-space-100)', alignItems: 'center' }}
                  >
                    <InsertDriveFile color="action" fontSize="small" />
                    <Typography variant="caption" color="text.secondary">
                      {t('uploader.fileName', 'File Name')}
                    </Typography>
                  </Stack>
                  <Typography variant="caption" fontWeight={500}>
                    {summary?.fileName ||
                      (isUploading ? <Skeleton width={80} /> : '-')}
                  </Typography>
                </Box>
                <Divider
                  sx={{ borderColor: 'var(--ob-color-border-subtle)' }}
                />
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <Typography variant="caption" color="text.secondary">
                    {t('uploader.floorsDetected', 'Floors Detected')}
                  </Typography>
                  {detectedFloors.length > 0 ? (
                    <StatusChip
                      label={`${detectedFloors.length}`}
                      size="small"
                      status="success"
                    />
                  ) : isUploading ? (
                    <Skeleton width={30} />
                  ) : (
                    <Typography variant="caption" color="text.disabled">
                      -
                    </Typography>
                  )}
                </Box>
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <Typography variant="caption" color="text.secondary">
                    {t('uploader.unitsCount', 'Units Count')}
                  </Typography>
                  {detectedUnits.length > 0 ? (
                    <StatusChip
                      label={`${detectedUnits.length}`}
                      size="small"
                      status="success"
                    />
                  ) : isUploading ? (
                    <Skeleton width={30} />
                  ) : (
                    <Typography variant="caption" color="text.disabled">
                      -
                    </Typography>
                  )}
                </Box>
              </Stack>
            </GlassCard>
          </Stack>
        </Grid>
      </Grid>
    </Box>
  )
}

export default CadUploader
