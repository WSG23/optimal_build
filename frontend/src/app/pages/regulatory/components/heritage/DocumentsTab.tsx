import React from 'react'
import {
  Alert,
  Box,
  Checkbox,
  Chip,
  FormControlLabel,
  Grid,
  Paper,
  Typography,
} from '@mui/material'
import UploadIcon from '@mui/icons-material/Upload'

interface DocumentsTabProps {
  conservationPlanAttached: boolean
  onConservationPlanChange: (checked: boolean) => void
  uploadedPhotos: string[]
  uploadedDrawings: string[]
  onPhotoUpload: () => void
  onDrawingUpload: () => void
  onRemovePhoto: (index: number) => void
  onRemoveDrawing: (index: number) => void
  isSubmitted: boolean
}

export function DocumentsTab({
  conservationPlanAttached,
  onConservationPlanChange,
  uploadedPhotos,
  uploadedDrawings,
  onPhotoUpload,
  onDrawingUpload,
  onRemovePhoto,
  onRemoveDrawing,
  isSubmitted,
}: DocumentsTabProps) {
  return (
    <>
      <Typography variant="subtitle1" gutterBottom>
        Required Documents
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Upload supporting documents for your heritage submission.
      </Typography>

      <Grid container spacing={2}>
        <Grid item xs={12}>
          <Paper
            sx={{
              p: 2,
              bgcolor: 'rgba(255, 255, 255, 0.03)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
            }}
          >
            <FormControlLabel
              control={
                <Checkbox
                  checked={conservationPlanAttached}
                  onChange={(e) => {
                    onConservationPlanChange(e.target.checked)
                  }}
                  disabled={isSubmitted}
                />
              }
              label={
                <Box>
                  <Typography variant="body1">
                    Conservation Management Plan
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Detailed plan for preserving heritage significance (Required
                    for National Monuments)
                  </Typography>
                </Box>
              }
            />
          </Paper>
        </Grid>

        <Grid item xs={12} sm={6}>
          <Paper
            onClick={onPhotoUpload}
            sx={{
              p: 3,
              textAlign: 'center',
              border: '2px dashed',
              borderColor:
                uploadedPhotos.length > 0
                  ? 'success.main'
                  : 'rgba(255, 255, 255, 0.2)',
              cursor: isSubmitted ? 'default' : 'pointer',
              bgcolor:
                uploadedPhotos.length > 0
                  ? 'rgba(46, 125, 50, 0.1)'
                  : 'transparent',
              '&:hover': isSubmitted
                ? {}
                : {
                    bgcolor: 'rgba(255, 255, 255, 0.05)',
                    borderColor: 'primary.main',
                  },
            }}
          >
            <UploadIcon
              sx={{
                fontSize: 40,
                color:
                  uploadedPhotos.length > 0 ? 'success.main' : 'text.secondary',
                mb: 1,
              }}
            />
            <Typography variant="body2">Upload Historical Photos</Typography>
            <Typography variant="caption" color="text.secondary">
              Original photographs, archival images
            </Typography>
            {uploadedPhotos.length > 0 && (
              <Box sx={{ mt: 2, textAlign: 'left' }}>
                {uploadedPhotos.map((file, idx) => (
                  <Chip
                    key={idx}
                    label={file}
                    size="small"
                    onDelete={
                      isSubmitted
                        ? undefined
                        : () => {
                            onRemovePhoto(idx)
                          }
                    }
                    sx={{ m: 0.5 }}
                  />
                ))}
              </Box>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} sm={6}>
          <Paper
            onClick={onDrawingUpload}
            sx={{
              p: 3,
              textAlign: 'center',
              border: '2px dashed',
              borderColor:
                uploadedDrawings.length > 0
                  ? 'success.main'
                  : 'rgba(255, 255, 255, 0.2)',
              cursor: isSubmitted ? 'default' : 'pointer',
              bgcolor:
                uploadedDrawings.length > 0
                  ? 'rgba(46, 125, 50, 0.1)'
                  : 'transparent',
              '&:hover': isSubmitted
                ? {}
                : {
                    bgcolor: 'rgba(255, 255, 255, 0.05)',
                    borderColor: 'primary.main',
                  },
            }}
          >
            <UploadIcon
              sx={{
                fontSize: 40,
                color:
                  uploadedDrawings.length > 0
                    ? 'success.main'
                    : 'text.secondary',
                mb: 1,
              }}
            />
            <Typography variant="body2">
              Upload Architectural Drawings
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Plans, elevations, sections
            </Typography>
            {uploadedDrawings.length > 0 && (
              <Box sx={{ mt: 2, textAlign: 'left' }}>
                {uploadedDrawings.map((file, idx) => (
                  <Chip
                    key={idx}
                    label={file}
                    size="small"
                    onDelete={
                      isSubmitted
                        ? undefined
                        : () => {
                            onRemoveDrawing(idx)
                          }
                    }
                    sx={{ m: 0.5 }}
                  />
                ))}
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>

      <Alert severity="info" sx={{ mt: 3 }}>
        <Typography variant="body2">
          Document upload is simulated in this demo. Files are tracked locally
          but not persisted to the server. In production, files would be
          uploaded to secure storage and attached to the submission.
        </Typography>
      </Alert>
    </>
  )
}
