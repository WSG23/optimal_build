import type { SiteAcquisitionResult } from '../../../../api/siteAcquisition'
import type { DevelopmentScenario } from '../../../../api/agents'

const STORAGE_PREFIX = 'ob_capture_project'
const OVERRIDE_STORAGE_PREFIX = 'ob_capture_override'

type StoredCapturePayload = {
  projectId: string
  propertyId: string
  savedAt: string
  result: SiteAcquisitionResult
}

function buildStorageKey(projectId: string): string {
  return `${STORAGE_PREFIX}:${projectId}`
}

function buildOverrideStorageKey(projectId: string): string {
  return `${OVERRIDE_STORAGE_PREFIX}:${projectId}`
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

export function saveCaptureScenarioOverrideForProject(
  projectId: string,
  scenario: DevelopmentScenario,
): void {
  if (typeof window === 'undefined') {
    return
  }
  if (!projectId || !scenario) {
    return
  }
  window.localStorage.setItem(
    buildOverrideStorageKey(projectId),
    JSON.stringify({
      projectId,
      scenario,
      savedAt: new Date().toISOString(),
    }),
  )
}

export function loadCaptureScenarioOverrideForProject(
  projectId: string,
): DevelopmentScenario | null {
  if (typeof window === 'undefined') {
    return null
  }
  if (!projectId) {
    return null
  }
  const raw = window.localStorage.getItem(buildOverrideStorageKey(projectId))
  if (!raw) {
    return null
  }
  try {
    const parsed = JSON.parse(raw) as {
      projectId?: string
      scenario?: DevelopmentScenario
    }
    if (parsed?.projectId !== projectId || !parsed?.scenario) {
      return null
    }
    return parsed.scenario
  } catch {
    return null
  }
}

export function clearCaptureScenarioOverrideForProject(
  projectId: string,
): void {
  if (typeof window === 'undefined') {
    return
  }
  if (!projectId) {
    return
  }
  window.localStorage.removeItem(buildOverrideStorageKey(projectId))
}
