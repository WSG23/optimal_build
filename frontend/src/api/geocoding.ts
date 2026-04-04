import { buildUrl } from './shared'
import {
  mapExternalSourceMetadata,
  type ExternalSourceMetadata,
} from './externalSources'

export interface GeocodeResult {
  latitude: number
  longitude: number
  formattedAddress: string
  source?: ExternalSourceMetadata | null
}

export async function forwardGeocodeAddress(
  address: string,
): Promise<GeocodeResult> {
  const encoded = encodeURIComponent(address)
  const url = buildUrl(`/api/v1/geocoding/forward?address=${encoded}`)
  const response = await fetch(url)
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || `Geocoding failed with status ${response.status}`)
  }
  const payload = (await response.json()) as {
    latitude?: number
    longitude?: number
    formattedAddress?: string
    formatted_address?: string
    source?: unknown
  }
  if (payload.latitude == null || payload.longitude == null) {
    throw new Error('Geocode result missing coordinates')
  }
  const formatted =
    payload.formattedAddress || payload.formatted_address || address
  return {
    latitude: payload.latitude,
    longitude: payload.longitude,
    formattedAddress: formatted,
    source: mapExternalSourceMetadata(payload.source),
  }
}

export async function reverseGeocodeCoords(
  latitude: number,
  longitude: number,
): Promise<GeocodeResult> {
  const url = buildUrl(
    `/api/v1/geocoding/reverse?latitude=${latitude}&longitude=${longitude}`,
  )
  const response = await fetch(url)
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(
      detail || `Reverse geocoding failed with status ${response.status}`,
    )
  }
  const payload = (await response.json()) as {
    latitude?: number
    longitude?: number
    formattedAddress?: string
    formatted_address?: string
    source?: unknown
  }
  if (payload.latitude == null || payload.longitude == null) {
    throw new Error('Reverse geocode result missing coordinates')
  }
  const formatted =
    payload.formattedAddress ||
    payload.formatted_address ||
    `${latitude}, ${longitude}`
  return {
    latitude: payload.latitude ?? latitude,
    longitude: payload.longitude ?? longitude,
    formattedAddress: formatted,
    source: mapExternalSourceMetadata(payload.source),
  }
}
