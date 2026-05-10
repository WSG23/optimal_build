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

export interface ForwardGeocodeOptions {
  jurisdictionCode?: string | null
}

export async function forwardGeocodeAddress(
  address: string,
  options: ForwardGeocodeOptions = {},
): Promise<GeocodeResult> {
  const params = new URLSearchParams({ address })
  if (options.jurisdictionCode) {
    params.set('jurisdictionCode', options.jurisdictionCode)
  }
  const url = buildUrl(`/api/v1/geocoding/forward?${params.toString()}`)
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(await geocodingErrorMessage(response, 'Geocoding failed'))
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
    throw new Error(
      await geocodingErrorMessage(response, 'Reverse geocoding failed'),
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

async function geocodingErrorMessage(
  response: Response,
  fallback: string,
): Promise<string> {
  const body = await response.text()
  if (body) {
    try {
      const payload = JSON.parse(body) as { detail?: unknown; title?: unknown }
      if (typeof payload.detail === 'string' && payload.detail.trim()) {
        return payload.detail
      }
      if (typeof payload.title === 'string' && payload.title.trim()) {
        return payload.title
      }
    } catch {
      return body
    }
    return body
  }
  return `${fallback} with status ${response.status}`
}
