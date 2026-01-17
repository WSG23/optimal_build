import {
  Box,
  Typography,
  Grid,
  TextField,
  MenuItem,
  CircularProgress,
  Avatar,
  Stack,
} from '@mui/material'
import { GlassCard } from '../../../components/canonical/GlassCard'
import { GlassButton } from '../../../components/canonical/GlassButton'
import type { AdvisoryFeedbackItem } from '../../api/advisory'
import type { FormEvent } from 'react'

interface FeedbackFormProps {
  sentiment: string
  notes: string
  isSubmitting: boolean
  feedbackHistory: AdvisoryFeedbackItem[]
  onSentimentChange: (val: string) => void
  onNotesChange: (val: string) => void
  onSubmit: (e: FormEvent<HTMLFormElement>) => void
}

export function FeedbackForm({
  sentiment,
  notes,
  isSubmitting,
  feedbackHistory,
  onSentimentChange,
  onNotesChange,
  onSubmit,
}: FeedbackFormProps) {
  return (
    <Grid container spacing={4}>
      <Grid item xs={12} md={6}>
        <GlassCard className="advisory-panel" sx={{ height: '100%' }}>
          <Box
            sx={{
              p: 2,
              borderBottom: '1px solid var(--ob-color-border-subtle)',
            }}
          >
            <Typography variant="h6" sx={{ fontSize: '1rem', fontWeight: 600 }}>
              Provide Feedback
            </Typography>
          </Box>
          <Box sx={{ p: 3 }} component="form" onSubmit={onSubmit}>
            <TextField
              select
              label="Sentiment"
              fullWidth
              value={sentiment}
              onChange={(e) => onSentimentChange(e.target.value)}
              disabled={isSubmitting}
              sx={{ mb: 3 }}
              variant="outlined"
            >
              <MenuItem value="positive">Positive</MenuItem>
              <MenuItem value="neutral">Neutral</MenuItem>
              <MenuItem value="negative">Negative</MenuItem>
            </TextField>

            <TextField
              label="Notes"
              fullWidth
              multiline
              rows={4}
              value={notes}
              onChange={(e) => onNotesChange(e.target.value)}
              disabled={isSubmitting}
              placeholder="Share your thoughts on this advisory plan..."
              sx={{ mb: 3 }}
              variant="outlined"
            />

            <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
              <GlassButton
                type="submit"
                variant="glow"
                disabled={isSubmitting || !notes.trim()}
              >
                {isSubmitting ? (
                  <>
                    <CircularProgress size={16} sx={{ mr: 1 }} /> Submitting...
                  </>
                ) : (
                  'Record Feedback'
                )}
              </GlassButton>
            </Box>
          </Box>
        </GlassCard>
      </Grid>

      <Grid item xs={12} md={6}>
        <GlassCard className="advisory-panel" sx={{ height: '100%' }}>
          <Box
            sx={{
              p: 2,
              borderBottom: '1px solid var(--ob-color-border-subtle)',
            }}
          >
            <Typography variant="h6" sx={{ fontSize: '1rem', fontWeight: 600 }}>
              Recent Activity
            </Typography>
          </Box>
          <Box sx={{ p: 3, maxHeight: 400, overflowY: 'auto' }}>
            {feedbackHistory.length === 0 ? (
              <Typography
                sx={{
                  color: 'var(--ob-color-text-muted)',
                  fontStyle: 'italic',
                  textAlign: 'center',
                  mt: 4,
                }}
              >
                No feedback recorded yet.
              </Typography>
            ) : (
              <Stack spacing={2}>
                {feedbackHistory.map((item) => (
                  <Box
                    key={item.id}
                    sx={{
                      p: 2,
                      borderRadius: 'var(--ob-radius-sm)',
                      bgcolor: 'rgba(255,255,255,0.03)',
                      border: '1px solid var(--ob-color-border-subtle)',
                    }}
                  >
                    <Box
                      sx={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        mb: 1,
                      }}
                    >
                      <Typography
                        variant="caption"
                        sx={{
                          fontWeight: 700,
                          textTransform: 'uppercase',
                          color:
                            item.sentiment === 'positive'
                              ? 'var(--ob-color-success)'
                              : item.sentiment === 'negative'
                                ? 'var(--ob-color-error)'
                                : 'var(--ob-color-warning)',
                        }}
                      >
                        {item.sentiment}
                      </Typography>
                      <Typography
                        variant="caption"
                        sx={{ color: 'var(--ob-color-text-secondary)' }}
                      >
                        {new Date(item.created_at).toLocaleDateString()}
                      </Typography>
                    </Box>
                    <Typography variant="body2">{item.notes}</Typography>
                  </Box>
                ))}
              </Stack>
            )}
          </Box>
        </GlassCard>
      </Grid>
    </Grid>
  )
}
