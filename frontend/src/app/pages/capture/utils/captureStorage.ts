import type { SiteAcquisitionResult } from '../../../../api/siteAcquisition'

const STORAGE_PREFIX = 'ob_capture_project'

type StoredCapturePayload = {
  projectId: string
  propertyId: string
  savedAt: string
  result: SiteAcquisitionResult
}

function buildStorageKey(projectId: string): string {
  return `${STORAGE_PREFIX}:${projectId}`
}

export function saveCaptureForProject(
  projectId: string,
  result: SiteAcquisitionResult,
): void {
  if (typeof window === 'undefined') {
    return
  }
  if (!projectId || !result?.propertyId) {
    return
  }
  const payload: StoredCapturePayload = {
    projectId,
    propertyId: result.propertyId,
    savedAt: new Date().toISOString(),
    result,
  }
  window.localStorage.setItem(
    buildStorageKey(projectId),
    JSON.stringify(payload),
  )
}

export function loadCaptureForProject(
  projectId: string,
): SiteAcquisitionResult | null {
  if (typeof window === 'undefined') {
    return null
  }
  if (!projectId) {
    return null
  }
  const raw = window.localStorage.getItem(buildStorageKey(projectId))
  if (!raw) {
    return null
  }
  try {
    const parsed = JSON.parse(raw) as StoredCapturePayload
    if (parsed?.projectId !== projectId || !parsed?.result) {
      return null
    }
    return parsed.result
  } catch {
    return null
  }
}

export function getCapturePropertyId(projectId: string): string | null {
  if (typeof window === 'undefined') {
    return null
  }
  if (!projectId) {
    return null
  }
  const raw = window.localStorage.getItem(buildStorageKey(projectId))
  if (!raw) {
    return null
  }
  try {
    const parsed = JSON.parse(raw) as StoredCapturePayload
    if (parsed?.projectId !== projectId || !parsed?.propertyId) {
      return null
    }
    return parsed.propertyId
  } catch {
    return null
  }
}
