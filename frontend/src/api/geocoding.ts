import { buildUrl } from './shared'

export interface GeocodeResult {
  latitude: number
  longitude: number
  formattedAddress: string
}

export interface SmartSearchSuggestion {
  address: string
  latitude: number
  longitude: number
  zoning?: string | null
  zoningDescription?: string | null
  siteArea?: number | null
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
  }
}

export async function fetchSmartSearchSuggestions(
  address: string,
  signal?: AbortSignal,
): Promise<SmartSearchSuggestion[]> {
  const encoded = encodeURIComponent(address)
  const url = buildUrl(`/api/v1/geocoding/suggestions?address=${encoded}`)
  const response = await fetch(url, { signal })
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(
      detail || `Smart search failed with status ${response.status}`,
    )
  }
  const payload = (await response.json()) as Array<{
    address?: string
    latitude?: number
    longitude?: number
    zoning?: string | null
    zoningDescription?: string | null
    zoning_description?: string | null
    siteArea?: number | null
    site_area_sqm?: number | null
  }>

  if (!Array.isArray(payload)) {
    return []
  }

  return payload
    .map((item) => ({
      address: String(item.address ?? ''),
      latitude: Number(item.latitude ?? 0),
      longitude: Number(item.longitude ?? 0),
      zoning: item.zoning ?? null,
      zoningDescription:
        item.zoningDescription ?? item.zoning_description ?? null,
      siteArea: item.siteArea ?? item.site_area_sqm ?? null,
    }))
    .filter(
      (item) =>
        item.address &&
        Number.isFinite(item.latitude) &&
        Number.isFinite(item.longitude),
    )
}
