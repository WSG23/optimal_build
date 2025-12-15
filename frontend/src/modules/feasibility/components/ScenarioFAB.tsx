import { AutoAwesome } from '@mui/icons-material'
import { Button, CircularProgress, keyframes, Box } from '@mui/material'

interface ScenarioFABProps {
  label: string
  onClick: () => void
  disabled?: boolean
  loading?: boolean
}

const pulse = keyframes`
  0% { box-shadow: 0 0 0 0 rgba(0, 255, 255, 0.4); }
  70% { box-shadow: 0 0 0 10px rgba(0, 255, 255, 0); }
  100% { box-shadow: 0 0 0 0 rgba(0, 255, 255, 0); }
`

export function ScenarioFAB({
  label,
  onClick,
  disabled,
  loading,
}: ScenarioFABProps) {
  return (
    <Box
      sx={{ width: '100%', display: 'flex', justifyContent: 'center', p: 1 }}
    >
      <Button
        onClick={onClick}
        disabled={disabled || loading}
        fullWidth
        variant="contained"
        data-testid="compute-button"
        startIcon={
          loading ? (
            <CircularProgress size={20} color="inherit" />
          ) : (
            <AutoAwesome />
          )
        }
        sx={{
          background: 'linear-gradient(135deg, #00C6FF 0%, #0072FF 100%)', // Electric Blue
          color: 'white',
          fontWeight: 700,
          fontSize: '1rem',
          textTransform: 'none',
          py: 1.5,
          borderRadius: '2px', // Square Cyber-Minimalism: xs for buttons
          boxShadow: '0 4px 15px rgba(0, 114, 255, 0.4)',
          position: 'relative',
          overflow: 'hidden',
          transition: 'all 0.3s ease',
          '&:hover': {
            background: 'linear-gradient(135deg, #00D2FF 0%, #0084FF 100%)',
            boxShadow: '0 6px 20px rgba(0, 114, 255, 0.6)',
            transform: 'translateY(-2px)',
          },
          '&:active': {
            transform: 'translateY(1px)',
          },
          '&.Mui-disabled': {
            background: 'rgba(255, 255, 255, 0.12)',
            color: 'rgba(255, 255, 255, 0.3)',
          },
          // Glow effect animation
          animation: !disabled && !loading ? `${pulse} 2s infinite` : 'none',
        }}
      >
        {loading ? (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <span>Constructing Scenario...</span>
          </Box>
        ) : (
          label
        )}
      </Button>
    </Box>
  )
}
