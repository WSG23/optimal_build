import React, { useEffect, useMemo, useRef, useState } from 'react'
import { Box, Paper, Typography } from '@mui/material'
import { MarketTransaction } from '../../../types/market'
import { PropertyType } from '../../../types/property'

const GOOGLE_MAPS_API_KEY = import.meta.env?.VITE_GOOGLE_MAPS_API_KEY ?? ''

interface MarketHeatmapProps {
  transactions: MarketTransaction[]
  propertyType: PropertyType
}

// Track if Google Maps script is loading/loaded
let googleMapsPromise: Promise<void> | null = null

function loadGoogleMapsScript(): Promise<void> {
  if (window.google?.maps) {
    return Promise.resolve()
  }

  if (googleMapsPromise) {
    return googleMapsPromise
  }

  googleMapsPromise = new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = `https://maps.googleapis.com/maps/api/js?key=${GOOGLE_MAPS_API_KEY}&libraries=visualization&loading=async`
    script.async = true
    script.defer = true
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('Failed to load Google Maps'))
    document.head.appendChild(script)
  })

  return googleMapsPromise
}

const MarketHeatmap: React.FC<MarketHeatmapProps> = ({
  transactions,
  propertyType,
}) => {
  const mapContainer = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<google.maps.Map | null>(null)
  const heatmapRef = useRef<google.maps.visualization.HeatmapLayer | null>(null)
  const markersRef = useRef<google.maps.marker.AdvancedMarkerElement[]>([])
  const infoWindowRef = useRef<google.maps.InfoWindow | null>(null)
  const [isLoaded, setIsLoaded] = useState(false)
  const [loadError, setLoadError] = useState<string | null>(null)

  const filteredTransactions = useMemo(
    () =>
      transactions.filter(
        (transaction) => transaction.property_type === propertyType,
      ),
    [transactions, propertyType],
  )

  // Generate heatmap data points
  const heatmapData = useMemo(() => {
    if (!window.google?.maps) return []

    const singaporeBounds = {
      minLng: 103.6,
      maxLng: 104.0,
      minLat: 1.2,
      maxLat: 1.5,
    }

    return filteredTransactions.map((transaction) => {
      const lng =
        singaporeBounds.minLng +
        Math.random() * (singaporeBounds.maxLng - singaporeBounds.minLng)
      const lat =
        singaporeBounds.minLat +
        Math.random() * (singaporeBounds.maxLat - singaporeBounds.minLat)

      return {
        location: new google.maps.LatLng(lat, lng),
        weight: Math.min(transaction.sale_price / 1000000, 10), // Normalize weight
        transaction,
      }
    })
  }, [filteredTransactions, isLoaded]) // eslint-disable-line react-hooks/exhaustive-deps

  // Load Google Maps script
  useEffect(() => {
    if (!GOOGLE_MAPS_API_KEY) {
      setLoadError('Google Maps API key not configured')
      return
    }

    loadGoogleMapsScript()
      .then(() => setIsLoaded(true))
      .catch((err) => setLoadError(err.message))
  }, [])

  // Initialize map
  useEffect(() => {
    if (!isLoaded || !mapContainer.current || mapRef.current) return

    // Dark mode map style
    const darkMapStyle: google.maps.MapTypeStyle[] = [
      { elementType: 'geometry', stylers: [{ color: '#242f3e' }] },
      { elementType: 'labels.text.stroke', stylers: [{ color: '#242f3e' }] },
      { elementType: 'labels.text.fill', stylers: [{ color: '#746855' }] },
      {
        featureType: 'administrative.locality',
        elementType: 'labels.text.fill',
        stylers: [{ color: '#d59563' }],
      },
      {
        featureType: 'poi',
        elementType: 'labels.text.fill',
        stylers: [{ color: '#d59563' }],
      },
      {
        featureType: 'poi.park',
        elementType: 'geometry',
        stylers: [{ color: '#263c3f' }],
      },
      {
        featureType: 'poi.park',
        elementType: 'labels.text.fill',
        stylers: [{ color: '#6b9a76' }],
      },
      {
        featureType: 'road',
        elementType: 'geometry',
        stylers: [{ color: '#38414e' }],
      },
      {
        featureType: 'road',
        elementType: 'geometry.stroke',
        stylers: [{ color: '#212a37' }],
      },
      {
        featureType: 'road',
        elementType: 'labels.text.fill',
        stylers: [{ color: '#9ca5b3' }],
      },
      {
        featureType: 'road.highway',
        elementType: 'geometry',
        stylers: [{ color: '#746855' }],
      },
      {
        featureType: 'road.highway',
        elementType: 'geometry.stroke',
        stylers: [{ color: '#1f2835' }],
      },
      {
        featureType: 'road.highway',
        elementType: 'labels.text.fill',
        stylers: [{ color: '#f3d19c' }],
      },
      {
        featureType: 'transit',
        elementType: 'geometry',
        stylers: [{ color: '#2f3948' }],
      },
      {
        featureType: 'transit.station',
        elementType: 'labels.text.fill',
        stylers: [{ color: '#d59563' }],
      },
      {
        featureType: 'water',
        elementType: 'geometry',
        stylers: [{ color: '#17263c' }],
      },
      {
        featureType: 'water',
        elementType: 'labels.text.fill',
        stylers: [{ color: '#515c6d' }],
      },
      {
        featureType: 'water',
        elementType: 'labels.text.stroke',
        stylers: [{ color: '#17263c' }],
      },
    ]

    mapRef.current = new google.maps.Map(mapContainer.current, {
      center: { lat: 1.3521, lng: 103.8198 },
      zoom: 'var(--ob-space-800)',
      styles: darkMapStyle,
      mapTypeControl: false,
      streetViewControl: false,
    })

    // Create shared InfoWindow
    infoWindowRef.current = new google.maps.InfoWindow()

    return () => {
      if (mapRef.current) {
        // Cleanup markers
        markersRef.current.forEach((marker) => (marker.map = null))
        markersRef.current = []
        if (heatmapRef.current) {
          heatmapRef.current.setMap(null)
        }
      }
    }
  }, [isLoaded])

  // Update heatmap and markers when data changes
  useEffect(() => {
    if (!mapRef.current || !isLoaded || heatmapData.length === 0) return

    // Clear existing markers
    markersRef.current.forEach((marker) => (marker.map = null))
    markersRef.current = []

    // Create heatmap layer
    if (heatmapRef.current) {
      heatmapRef.current.setMap(null)
    }

    const heatmapPoints = heatmapData.map((point) => ({
      location: point.location,
      weight: point.weight,
    }))

    heatmapRef.current = new google.maps.visualization.HeatmapLayer({
      data: heatmapPoints,
      map: mapRef.current,
      radius: 30,
      opacity: 0.7,
      gradient: [
        'rgba(0, 0, 0, 0)',
        'rgba(50, 100, 200, 0.6)',
        'rgba(50, 150, 200, 0.7)',
        'rgba(50, 200, 150, 0.8)',
        'rgba(200, 200, 50, 0.9)',
        'rgba(200, 100, 50, 1)',
      ],
    })

    // Add click listeners for each data point (using invisible markers for interaction)
    heatmapData.forEach((point) => {
      const marker = new google.maps.marker.AdvancedMarkerElement({
        position: point.location,
        map: mapRef.current,
        content: createMarkerContent(),
      })

      marker.addListener('click', () => {
        if (!infoWindowRef.current || !mapRef.current) return

        const { transaction } = point
        const formattedPsf =
          transaction.psf_price !== null && transaction.psf_price !== undefined
            ? new Intl.NumberFormat('en-SG').format(transaction.psf_price)
            : 'N/A'

        infoWindowRef.current.setContent(`
          <div style="color: #333; padding: 8px;">
            <strong>${transaction.property_name}</strong><br/>
            Price: $${new Intl.NumberFormat('en-SG').format(transaction.sale_price)}<br/>
            PSF: $${formattedPsf}<br/>
            Date: ${new Date(transaction.transaction_date).toLocaleDateString()}
          </div>
        `)
        infoWindowRef.current.open(mapRef.current, marker)
      })

      markersRef.current.push(marker)
    })
  }, [heatmapData, isLoaded])

  if (loadError) {
    return (
      <Paper sx={{ p: 'var(--ob-space-300)', height: 500 }}>
        <Typography variant="body1" color="textSecondary" align="center">
          {loadError === 'Google Maps API key not configured'
            ? 'Map requires Google Maps API key. Set VITE_GOOGLE_MAPS_API_KEY in environment.'
            : `Failed to load map: ${loadError}`}
        </Typography>
      </Paper>
    )
  }

  if (!isLoaded) {
    return (
      <Paper sx={{ p: 'var(--ob-space-300)', height: 500 }}>
        <Typography variant="body1" color="textSecondary" align="center">
          Loading map...
        </Typography>
      </Paper>
    )
  }

  return (
    <Paper sx={{ p: 'var(--ob-space-200)', height: 500 }}>
      <Typography variant="h6" gutterBottom>
        Transaction Heatmap
      </Typography>
      <Box
        ref={mapContainer}
        sx={{
          height: 450,
          borderRadius: 'var(--ob-radius-sm)',
          overflow: 'hidden',
        }}
      />
    </Paper>
  )
}

// Create a small invisible marker element for click detection
function createMarkerContent(): HTMLElement {
  const div = document.createElement('div')
  div.style.width = '20px'
  div.style.height = '20px'
  div.style.borderRadius = '50%'
  div.style.cursor = 'pointer'
  div.style.opacity = '0' // Invisible but clickable
  return div
}

export default MarketHeatmap
