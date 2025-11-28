const GOOGLE_API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || ''

export interface GeocodeResult {
  latitude: number
  longitude: number
  formattedAddress: string
}

export async function forwardGeocodeAddress(address: string): Promise<GeocodeResult> {
  if (!GOOGLE_API_KEY) {
    throw new Error('Missing VITE_GOOGLE_MAPS_API_KEY')
  }
  const encoded = encodeURIComponent(address)
  const url = `https://maps.googleapis.com/maps/api/geocode/json?address=${encoded}&key=${GOOGLE_API_KEY}`
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`Geocoding failed with status ${response.status}`)
  }
  const payload = (await response.json()) as {
    results?: Array<{
      formatted_address?: string
      geometry?: { location?: { lat?: number; lng?: number } }
    }>
    status?: string
    error_message?: string
  }
  if (payload.status !== 'OK' || !payload.results?.length) {
    throw new Error(payload.error_message || 'No results for this address')
  }
  const first = payload.results[0]
  const loc = first.geometry?.location
  if (!loc?.lat || !loc?.lng) {
    throw new Error('Geocode result missing coordinates')
  }
  return {
    latitude: loc.lat,
    longitude: loc.lng,
    formattedAddress: first.formatted_address || address,
  }
}

export async function reverseGeocodeCoords(
  latitude: number,
  longitude: number,
): Promise<GeocodeResult> {
  if (!GOOGLE_API_KEY) {
    throw new Error('Missing VITE_GOOGLE_MAPS_API_KEY')
  }
  const url = `https://maps.googleapis.com/maps/api/geocode/json?latlng=${latitude},${longitude}&key=${GOOGLE_API_KEY}`
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`Reverse geocoding failed with status ${response.status}`)
  }
  const payload = (await response.json()) as {
    results?: Array<{
      formatted_address?: string
      geometry?: { location?: { lat?: number; lng?: number } }
    }>
    status?: string
    error_message?: string
  }
  if (payload.status !== 'OK' || !payload.results?.length) {
    throw new Error(payload.error_message || 'No results for these coordinates')
  }
  const first = payload.results[0]
  const loc = first.geometry?.location
  return {
    latitude: loc?.lat ?? latitude,
    longitude: loc?.lng ?? longitude,
    formattedAddress: first.formatted_address || `${latitude}, ${longitude}`,
  }
}
