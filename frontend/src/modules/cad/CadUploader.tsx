import { ChangeEvent, DragEvent, useRef, useState } from 'react'
import {
  Box,
  Typography,
  Stack,
  Stepper,
  Step,
  StepLabel,
  Grid,
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
    <Box className="cad-uploader" sx={{ maxWidth: 1000, margin: '0 auto' }}>
      <Stack sx={{ gap: 'var(--ob-space-200)' }}>
        {/* Top: Compact Hero Drop Zone */}
        <GlassCard
          className="cad-drop-zone"
          onClick={!isUploading ? handleBrowse : undefined}
          onDrop={!isUploading ? handleDrop : undefined}
          onDragOver={!isUploading ? handleDragOver : undefined}
          onDragLeave={!isUploading ? handleDragLeave : undefined}
          sx={{
            minHeight: 120, // Reduced from 180
            p: 'var(--ob-space-300)',
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
              backgroundColor: !isUploading ? 'var(--ob-brand-50)' : undefined,
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
            direction="row"
            sx={{
              gap: 'var(--ob-space-200)',
              alignItems: 'center',
              textAlign: 'left',
            }}
          >
            <Box
              sx={{
                width: 48, // Reduced from 64
                height: 48,
                borderRadius: '50%',
                backgroundColor: 'var(--ob-brand-100)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--ob-brand-500)',
                flexShrink: 0,
              }}
            >
              {isUploading ? (
                <Box
                  className="dot-flashing"
                  sx={{ transform: 'scale(1.0)' }}
                />
              ) : (
                <CloudUpload sx={{ fontSize: 24 }} />
              )}
            </Box>
            <Box>
              <Typography
                variant="subtitle1"
                fontWeight={600}
                gutterBottom={false}
              >
                {isUploading
                  ? t('uploader.uploadingTitle', 'Uploading...')
                  : t('uploader.dropTitle', 'Upload CAD File')}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {isUploading
                  ? t('uploader.uploadingHint', 'Please wait...')
                  : t('uploader.dropHint', 'Drag & drop or click to browse')}
              </Typography>
            </Box>
            {!isUploading && (
              <Box
                sx={{
                  ml: 'var(--ob-space-200)',
                  borderLeft: '1px solid var(--ob-color-border-subtle)',
                  pl: 'var(--ob-space-200)',
                }}
              >
                <Typography variant="caption" color="text.disabled">
                  {t('uploader.supportedFormats', '.dxf, .ifc, .pdf')}
                </Typography>
              </Box>
            )}
          </Stack>
        </GlassCard>

        {/* Bottom: Active Job Strip - Compact Row */}
        {(isUploading || status || summary) && (
          <GlassCard sx={{ p: 'var(--ob-space-200)' }}>
            <Grid container spacing={2} alignItems="center">
              {/* File Info */}
              <Grid item xs={12} md={3}>
                <Stack
                  direction="row"
                  sx={{ gap: 'var(--ob-space-150)', alignItems: 'center' }}
                >
                  <Box
                    sx={{
                      width: 32,
                      height: 32,
                      borderRadius: 'var(--ob-radius-sm)',
                      bgcolor: 'action.hover',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <InsertDriveFile color="action" fontSize="small" />
                  </Box>
                  <Box sx={{ minWidth: 0 }}>
                    <Typography variant="body2" noWrap fontWeight={600}>
                      {summary?.fileName ||
                        (isUploading ? 'Uploading...' : 'Pending')}
                    </Typography>
                  </Box>
                </Stack>
              </Grid>

              {/* Progress Stepper - Compact */}
              <Grid item xs={12} md={6}>
                <Stepper
                  activeStep={activeStep}
                  alternativeLabel
                  sx={{
                    '& .MuiStepLabel-label': {
                      marginTop: '4px !important',
                      fontSize: '0.75rem',
                    },
                    '& .MuiStepIcon-root': { fontSize: '1.25rem' },
                  }}
                >
                  {steps.map((label) => (
                    <Step key={label}>
                      <StepLabel
                        StepIconProps={{
                          sx: {
                            '&.Mui-active': { color: 'var(--ob-brand-500)' },
                            '&.Mui-completed': {
                              color: 'var(--ob-success-500)',
                            },
                          },
                        }}
                      >
                        {label}
                      </StepLabel>
                    </Step>
                  ))}
                </Stepper>
              </Grid>

              {/* Specs / Status */}
              <Grid item xs={12} md={3}>
                <Stack
                  direction="row"
                  sx={{
                    gap: 'var(--ob-space-100)',
                    justifyContent: 'flex-end',
                    flexWrap: 'wrap',
                  }}
                >
                  {detectedFloors.length > 0 && (
                    <StatusChip size="sm" status="success">
                      {`${String(detectedFloors.length)} Flrs`}
                    </StatusChip>
                  )}
                  {detectedUnits.length > 0 && (
                    <StatusChip size="sm" status="success">
                      {`${String(detectedUnits.length)} Units`}
                    </StatusChip>
                  )}
                </Stack>
              </Grid>
            </Grid>

            {/* Error Message Row */}
            {status?.error && (
              <Box
                sx={{
                  mt: 'var(--ob-space-150)',
                  p: 'var(--ob-space-100)',
                  borderRadius: 'var(--ob-radius-sm)',
                  backgroundColor: 'var(--ob-error-muted)',
                  color: 'var(--ob-error-600)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--ob-space-100)',
                }}
              >
                <ErrorIcon fontSize="small" />
                <Typography variant="caption">{status.error}</Typography>
              </Box>
            )}
          </GlassCard>
        )}
      </Stack>
    </Box>
  )
}

export default CadUploader
