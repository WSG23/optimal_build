import { PropertyLocationMap } from '@/app/pages/site-acquisition/components/map/PropertyLocationMap'
import { Typography, Box } from '@mui/material'
import MapIcon from '@mui/icons-material/Map'

interface ImmersiveMapProps {
  latitude?: number
  longitude?: number
  onCoordinatesChange?: (lat: number, lng: number) => void
}

export function ImmersiveMap({
  latitude = 1.285,
  longitude = 103.854,
  onCoordinatesChange,
}: ImmersiveMapProps) {
  // Mock checking for token - in reality PropertyLocationMap might throw or error internally.
  // We'll wrap it in an error boundary conceptually, or just overlay if it fails.
  // For this "wow" demo, we'll assume if there's no API key in env, we go straight to fallback
  // to avoid the ugly error message.

  // Note: accessing env var in Vite
  const hasMapboxToken = !!import.meta.env.VITE_MAPBOX_ACCESS_TOKEN
  const hasGoogleToken = !!import.meta.env.VITE_GOOGLE_MAPS_API_KEY

  // If neither token is present, show the beautiful fallback immediately
  const showFallback = !hasMapboxToken && !hasGoogleToken

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
          height={1200} // Make it large enough to cover background
          showAmenities={false}
          showHeritage={false}
          onCoordinatesChange={(lat, lon) =>
            onCoordinatesChange?.(parseFloat(lat), parseFloat(lon))
          }
          // onError={() => setHasError(true)} // Hypothetical prop
        />
      ) : (
        <div
          style={{
            width: '100%',
            height: '100%',
            backgroundImage:
              'url(https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?q=80&w=2613&auto=format&fit=crop)', // Cinematic city
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            filter: 'brightness(0.4) saturate(1.2)', // Darkened for text readability
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Box
            sx={{
              backgroundColor: 'rgba(0,0,0,0.6)',
              backdropFilter: 'blur(10px)',
              padding: '24px 48px',
              borderRadius: '16px',
              border: '1px solid rgba(255,255,255,0.1)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              color: 'white',
            }}
          >
            <MapIcon sx={{ fontSize: 48, marginBottom: 2, opacity: 0.8 }} />
            <Typography
              variant="h6"
              sx={{ fontWeight: 600, letterSpacing: '0.05em' }}
            >
              IMMERSIVE MAP PREVIEW
            </Typography>
            <Typography variant="caption" sx={{ opacity: 0.6, marginTop: 1 }}>
              MAP_TOKEN_MISSING (Visual Fallback Active)
            </Typography>
          </Box>
        </div>
      )}

      {/* Decorative Overlay Gradients */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '150px',
          background:
            'linear-gradient(to bottom, rgba(0,0,0,0.8), transparent)',
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: '300px',
          background: 'linear-gradient(to top, #0f172a, transparent)', // Fade into the dark bg of app
          pointerEvents: 'none',
        }}
      />
    </div>
  )
}
