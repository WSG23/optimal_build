import { PropertyLocationMap } from '@/app/pages/site-acquisition/components/map/PropertyLocationMap'
import { Typography, Box, TextField, InputAdornment } from '@mui/material'
import SearchIcon from '@mui/icons-material/Search'
import ExploreIcon from '@mui/icons-material/Explore'

interface ImmersiveMapProps {
  latitude?: number
  longitude?: number
  onCoordinatesChange?: (lat: number, lng: number) => void
  showCentralCTA?: boolean
  onAddressSearch?: (address: string) => void
}

export function ImmersiveMap({
  latitude = 1.285,
  longitude = 103.854,
  onCoordinatesChange,
  showCentralCTA = true,
  onAddressSearch,
}: ImmersiveMapProps) {
  const showFallback = false

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {!showFallback ? (
        <PropertyLocationMap
          latitude={latitude.toString()}
          longitude={longitude.toString()}
          interactive={true}
          height="100%"
          showAmenities={false}
          showHeritage={false}
          onCoordinatesChange={(lat, lon) =>
            onCoordinatesChange?.(parseFloat(lat), parseFloat(lon))
          }
        />
      ) : (
        /* Cinematic City Background with Slow Pan Animation */
        <div
          style={{
            width: '100%',
            height: '100%',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          {/* Animated background layer */}
          <div
            style={{
              position: 'absolute',
              inset: '-10%',
              backgroundImage:
                'url(https://images.unsplash.com/photo-1480714378408-67cf0d13bc1b?q=80&w=2940&auto=format&fit=crop)',
              backgroundSize: 'cover',
              backgroundPosition: 'center',
              filter: 'brightness(0.3) saturate(1.3)',
              animation: 'slowPan 60s ease-in-out infinite alternate',
            }}
          />
          <style>
            {`
              @keyframes slowPan {
                0% { transform: scale(1.1) translateX(0) translateY(0); }
                100% { transform: scale(1.15) translateX(-3%) translateY(-2%); }
              }
              @keyframes pulseGlow {
                0%, 100% { box-shadow: 0 0 40px var(--ob-color-neon-cyan-muted), 0 0 80px var(--ob-color-action-selected); }
                50% { box-shadow: 0 0 60px rgba(6, 182, 212, 0.5), 0 0 120px rgba(59, 130, 246, 0.3); }
              }
              @keyframes floatUp {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-8px); }
              }
            `}
          </style>

          {/* Grid overlay for tech feel */}
          <div
            style={{
              position: 'absolute',
              inset: 0,
              backgroundImage: `
                linear-gradient(rgba(6, 182, 212, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(6, 182, 212, 0.03) 1px, transparent 1px)
              `,
              backgroundSize: '50px 50px',
              pointerEvents: 'none',
            }}
          />
        </div>
      )}

      {/* Central CTA - "Unlock Site Intelligence" */}
      {showCentralCTA && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            pointerEvents: 'none',
            zIndex: 15,
          }}
        >
          <Box
            sx={{
              background: 'rgba(15, 23, 42, 0.85)',
              backdropFilter: 'blur(var(--ob-blur-lg))',
              border: '1px solid var(--ob-color-neon-cyan-muted)',
              borderRadius: 'var(--ob-radius-sm)',
              padding: '48px 64px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 'var(--ob-space-300)',
              maxWidth: '500px',
              animation:
                'floatUp 4s ease-in-out infinite, pulseGlow 3s ease-in-out infinite',
              pointerEvents: 'auto',
            }}
          >
            {/* Icon with glow */}
            <Box
              sx={{
                width: '80px',
                height: '80px',
                borderRadius: '50%',
                background:
                  'linear-gradient(135deg, var(--ob-color-neon-cyan-muted), var(--ob-color-action-selected))',
                border: '2px solid rgba(6, 182, 212, 0.4)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <ExploreIcon sx={{ fontSize: 40, color: '#06b6d4' }} />
            </Box>

            {/* Title */}
            <Typography
              variant="h4"
              sx={{
                fontWeight: 700,
                color: 'white',
                textAlign: 'center',
                letterSpacing: '-0.02em',
              }}
            >
              Unlock Site Intelligence
            </Typography>

            {/* Subtitle */}
            <Typography
              sx={{
                color: 'rgba(255,255,255,0.6)',
                textAlign: 'center',
                fontSize: '1rem',
                maxWidth: '380px',
              }}
            >
              Enter an address to visualize development potential, zoning
              constraints, and GFA optimization
            </Typography>

            {/* Search Input */}
            <TextField
              placeholder="Search for a location..."
              variant="outlined"
              fullWidth
              onKeyDown={(e) => {
                if (e.key === 'Enter' && onAddressSearch) {
                  onAddressSearch((e.target as HTMLInputElement).value)
                }
              }}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon
                      sx={{ color: 'var(--ob-color-text-tertiary)' }}
                    />
                  </InputAdornment>
                ),
              }}
              sx={{
                '& .MuiOutlinedInput-root': {
                  background: 'var(--ob-color-surface-overlay-light)',
                  borderRadius: 'var(--ob-radius-md)',
                  color: 'white',
                  fontSize: '1rem',
                  '& fieldset': {
                    borderColor: 'var(--ob-color-action-active)',
                  },
                  '&:hover fieldset': {
                    borderColor: 'rgba(6, 182, 212, 0.5)',
                  },
                  '&.Mui-focused fieldset': {
                    borderColor: '#06b6d4',
                  },
                },
                '& .MuiInputBase-input::placeholder': {
                  color: 'var(--ob-color-text-tertiary)',
                  opacity: 1,
                },
              }}
            />

            {/* Feature hints */}
            <Box
              sx={{
                display: 'flex',
                gap: 'var(--ob-space-200)',
                flexWrap: 'wrap',
                justifyContent: 'center',
              }}
            >
              {['Zoning Analysis', 'GFA Calculator', '3D Massing'].map(
                (feature) => (
                  <Box
                    key={feature}
                    sx={{
                      padding: '6px 12px',
                      borderRadius: 'var(--ob-radius-sm)',
                      background: 'var(--ob-color-action-selected)',
                      border: '1px solid var(--ob-color-neon-cyan-muted)',
                      color: 'rgba(6, 182, 212, 0.9)',
                      fontSize: '0.75rem',
                      fontWeight: 500,
                      textTransform: 'uppercase',
                      letterSpacing: '0.05em',
                    }}
                  >
                    {feature}
                  </Box>
                ),
              )}
            </Box>
          </Box>
        </div>
      )}

      {/* Decorative Overlay Gradients */}
      <div
        style={{
          position: 'absolute',
          top: '0',
          left: 0,
          right: 0,
          height: '150px',
          background:
            'linear-gradient(to bottom, var(--ob-color-overlay-backdrop-strong), transparent)',
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          bottom: '0',
          left: 0,
          right: 0,
          height: '300px',
          background: 'linear-gradient(to top, #0f172a, transparent)',
          pointerEvents: 'none',
        }}
      />
    </div>
  )
}
