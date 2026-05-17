import { Box, Checkbox, Grid, Typography } from '@mui/material'
import { GlassCard } from '../../../../../components/canonical/GlassCard'

const HERITAGE_ELEMENTS_OPTIONS = [
  { id: 'facade', label: 'Original Facade', category: 'Exterior' },
  { id: 'roof', label: 'Original Roof Form', category: 'Exterior' },
  { id: 'windows', label: 'Original Windows/Doors', category: 'Exterior' },
  { id: 'balcony', label: 'Balconies/Verandahs', category: 'Exterior' },
  { id: 'ornaments', label: 'Decorative Ornaments', category: 'Exterior' },
  { id: 'tiles', label: 'Original Floor Tiles', category: 'Interior' },
  { id: 'staircase', label: 'Original Staircase', category: 'Interior' },
  { id: 'columns', label: 'Columns/Pillars', category: 'Interior' },
  { id: 'ceiling', label: 'Ornate Ceilings', category: 'Interior' },
  { id: 'ironwork', label: 'Wrought Iron Work', category: 'Features' },
  { id: 'signage', label: 'Historic Signage', category: 'Features' },
  { id: 'garden', label: 'Heritage Garden/Landscape', category: 'Features' },
]

interface HeritageElementsTabProps {
  selectedElements: string[]
  onElementToggle: (elementId: string) => void
  isSubmitted: boolean
}

export function HeritageElementsTab({
  selectedElements,
  onElementToggle,
  isSubmitted,
}: HeritageElementsTabProps) {
  return (
    <>
      <Typography variant="subtitle1" gutterBottom>
        Select all heritage elements present in the building:
      </Typography>
      <Typography
        variant="body2"
        color="text.secondary"
        sx={{ mb: 'var(--ob-space-200)' }}
      >
        Identifying heritage elements helps STB understand the building&apos;s
        significance and guide appropriate conservation measures.
      </Typography>

      {['Exterior', 'Interior', 'Features'].map((category) => (
        <Box key={category} sx={{ mb: 'var(--ob-space-200)' }}>
          <Typography
            variant="subtitle2"
            color="primary"
            sx={{ mb: 'var(--ob-space-150)' }}
          >
            {category}
          </Typography>
          <Grid container spacing="var(--ob-space-100)">
            {HERITAGE_ELEMENTS_OPTIONS.filter(
              (el) => el.category === category,
            ).map((element) => (
              <Grid item xs={6} sm={4} md={3} key={element.id}>
                <GlassCard
                  onClick={() => {
                    if (!isSubmitted) onElementToggle(element.id)
                  }}
                  sx={{
                    p: 'var(--ob-space-150)',
                    cursor: isSubmitted ? 'default' : 'pointer',
                    bgcolor: selectedElements.includes(element.id)
                      ? 'rgba(46, 125, 50, 0.2)'
                      : 'rgba(245, 235, 220, 0.03)',
                    border: selectedElements.includes(element.id)
                      ? '1px solid rgba(46, 125, 50, 0.5)'
                      : '1px solid rgba(245, 235, 220, 0.1)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--ob-space-100)',
                    transition: 'all 0.2s',
                    '&:hover': {
                      bgcolor: isSubmitted
                        ? undefined
                        : selectedElements.includes(element.id)
                          ? 'rgba(46, 125, 50, 0.3)'
                          : 'rgba(245, 235, 220, 0.05)',
                    },
                  }}
                >
                  <Checkbox
                    checked={selectedElements.includes(element.id)}
                    disabled={isSubmitted}
                    size="small"
                    sx={{ p: 0 }}
                  />
                  <Typography variant="body2">{element.label}</Typography>
                </GlassCard>
              </Grid>
            ))}
          </Grid>
        </Box>
      ))}

      <Box sx={{ mt: 'var(--ob-space-200)' }}>
        <Typography variant="body2" color="text.secondary">
          Selected: {selectedElements.length} element(s)
        </Typography>
      </Box>
    </>
  )
}
