import { AutoAwesome, Business, Forest, Star } from '@mui/icons-material'
import { Card, CardActionArea, Typography, Grid } from '@mui/material'
import type { GenerativeStrategy } from '../types'
import { GENERATIVE_OPTIONS } from '../types'

interface GenerativeDesignPanelProps {
  selectedStrategy: GenerativeStrategy | null
  onSelectStrategy: (strategy: GenerativeStrategy) => void
  loading?: boolean
}

export function GenerativeDesignPanel({
  selectedStrategy,
  onSelectStrategy,
  loading = false,
}: GenerativeDesignPanelProps) {

  const getIcon = (strategy: GenerativeStrategy) => {
    switch (strategy) {
      case 'max_density': return <Business fontSize="large" />
      case 'balanced': return <AutoAwesome fontSize="large" />
      case 'iconic': return <Star fontSize="large" />
      case 'green_focus': return <Forest fontSize="large" />
      default: return <AutoAwesome fontSize="large" />
    }
  }

  return (
    <section className="feasibility-generative">
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '1rem' }}>
         <AutoAwesome sx={{ color: 'var(--ob-color-brand-primary)' }} />
         <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 600 }}>Generative Design</h2>
      </div>
      <p style={{ color: 'var(--ob-color-text-secondary)', marginBottom: '1.5rem' }}>
          AI-powered massing strategies optimized for your goals.
      </p>

      <Grid container spacing={2}>
        {GENERATIVE_OPTIONS.map((option) => {
          const isSelected = selectedStrategy === option.value
          return (
            <Grid item xs={6} key={option.value}>
              <Card
                variant="outlined"
                sx={{
                    height: '100%',
                    borderColor: isSelected ? 'var(--ob-color-brand-primary)' : undefined,
                    backgroundColor: isSelected ? 'rgba(59, 130, 246, 0.04)' : undefined,
                    transition: 'all 0.2s ease',
                    '&:hover': {
                        borderColor: 'var(--ob-color-brand-primary)',
                        transform: 'translateY(-2px)',
                        boxShadow: 'var(--ob-shadow-md)'
                    }
                }}
              >
                <CardActionArea
                    onClick={() => onSelectStrategy(option.value)}
                    disabled={loading}
                    sx={{ height: '100%', padding: '1rem' }}
                >
                  <div style={{
                      color: isSelected ? 'var(--ob-color-brand-primary)' : 'var(--ob-color-text-secondary)',
                      marginBottom: '0.5rem'
                  }}>
                      {getIcon(option.value)}
                  </div>
                  <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                    {option.label}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ lineHeight: 1.4, display: 'block' }}>
                    {option.description}
                  </Typography>
                </CardActionArea>
              </Card>
            </Grid>
          )
        })}
      </Grid>
    </section>
  )
}
