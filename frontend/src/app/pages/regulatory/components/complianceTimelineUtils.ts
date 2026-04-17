/**
 * Compliance Timeline Utilities
 *
 * Asset type resolution, storage, and normalization logic extracted
 * from CompliancePathTimeline for component size management.
 */

import type {
  AssetType,
  AuthoritySubmission,
  AssetCompliancePath,
} from '../../../../api/regulatory'
import { loadCaptureForProject } from '../../capture/utils/captureStorage'

// Status type for compliance steps
export type StepStatus = 'completed' | 'in_progress' | 'pending' | 'delayed'

export const ASSET_TYPE_OPTIONS: { value: AssetType; label: string }[] = [
  { value: 'office', label: 'Office' },
  { value: 'retail', label: 'Retail' },
  { value: 'residential', label: 'Residential' },
  { value: 'industrial', label: 'Industrial' },
  { value: 'hospitality', label: 'Hospitality' },
  { value: 'mixed_use', label: 'Mixed Use' },
  { value: 'heritage', label: 'Heritage / Conservation' },
]

// Submission type display names - includes both API values and legacy mock values
export const SUBMISSION_TYPE_LABELS: Record<string, string> = {
  // Actual API submission types
  DC: 'Development Control (URA)',
  BP: 'Building Plan (BCA)',
  TOP: 'Temporary Occupation Permit',
  CSC: 'Certificate of Statutory Completion',
  CONSULTATION: 'Agency Consultation',
  WAIVER: 'Waiver Application',
  HERITAGE_APPROVAL: 'Heritage Conservation (STB)',
  INDUSTRIAL_PERMIT: 'Industrial Permit (JTC)',
  CHANGE_OF_USE: 'Change of Use',
  // Legacy mock values (fallback)
  planning_permission: 'Planning Permission',
  development_control: 'Development Control',
  building_plan: 'Building Plan Approval',
  structural_plan: 'Structural Plan',
  fire_safety: 'Fire Safety Certificate',
  environmental: 'Environmental Clearance',
  heritage_conservation: 'Heritage Conservation',
  change_of_use: 'Change of Use',
  csc_application: 'CSC Application',
  top_application: 'TOP Application',
}

export const DAY_WIDTH = 8
export const ROW_HEIGHT = 56
export const LEFT_PANEL_WIDTH = 320

const ASSET_TYPE_STORAGE_PREFIX = 'ob_compliance_asset_type'

function storageKeyForProject(projectId: string): string {
  return `${ASSET_TYPE_STORAGE_PREFIX}:${projectId}`
}

export function readStoredAssetType(projectId?: string): AssetType | null {
  if (typeof window === 'undefined' || !projectId) {
    return null
  }
  const raw = window.localStorage.getItem(storageKeyForProject(projectId))
  if (!raw) {
    return null
  }
  const candidate = raw.trim().toLowerCase().replace(/[-\s]/g, '_')
  if (candidate === 'mixed') {
    return 'mixed_use'
  }
  if (candidate === 'conservation') {
    return 'heritage'
  }
  if (candidate === 'hotel') {
    return 'hospitality'
  }
  const allowed: AssetType[] = [
    'office',
    'retail',
    'residential',
    'industrial',
    'hospitality',
    'mixed_use',
    'heritage',
  ]
  return allowed.includes(candidate as AssetType)
    ? (candidate as AssetType)
    : null
}

export function persistAssetType(projectId: string, assetType: AssetType) {
  if (typeof window === 'undefined') {
    return
  }
  window.localStorage.setItem(storageKeyForProject(projectId), assetType)
}

export function normalizeAssetType(value?: string | null): AssetType | null {
  if (!value) {
    return null
  }
  const candidate = value.trim().toLowerCase().replace(/[-\s]/g, '_')
  if (candidate.includes('heritage') || candidate.includes('conservation')) {
    return 'heritage'
  }
  if (candidate.includes('mixed')) {
    return 'mixed_use'
  }
  if (candidate.includes('hospitality') || candidate.includes('hotel')) {
    return 'hospitality'
  }
  if (candidate.includes('industrial')) {
    return 'industrial'
  }
  if (candidate.includes('residential')) {
    return 'residential'
  }
  if (candidate.includes('retail')) {
    return 'retail'
  }
  if (candidate.includes('office')) {
    return 'office'
  }
  const allowed: AssetType[] = [
    'office',
    'retail',
    'residential',
    'industrial',
    'hospitality',
    'mixed_use',
    'heritage',
  ]
  return allowed.includes(candidate as AssetType)
    ? (candidate as AssetType)
    : null
}

type AssetTypeWeight = {
  assetType?: string | null
  allocationPct?: number | null
}

function pickDominantAssetType(items: AssetTypeWeight[]): AssetType | null {
  if (!items.length) {
    return null
  }
  const ranked = [...items].sort((a, b) => {
    const aWeight = a.allocationPct ?? 0
    const bWeight = b.allocationPct ?? 0
    return bWeight - aWeight
  })
  return normalizeAssetType(ranked[0]?.assetType ?? null)
}

export function deriveAssetTypeFromCapture(
  projectId?: string,
): AssetType | null {
  if (!projectId) {
    return null
  }
  const capture = loadCaptureForProject(projectId)
  if (!capture) {
    return null
  }
  if (capture.heritageContext?.flag) {
    return 'heritage'
  }
  const fromOptimizations = pickDominantAssetType(capture.optimizations ?? [])
  if (fromOptimizations) {
    return fromOptimizations
  }
  const fromLayers = pickDominantAssetType(
    capture.visualization?.massingLayers ?? [],
  )
  if (fromLayers) {
    return fromLayers
  }
  return normalizeAssetType(capture.existingUse)
}

// Get progress and status from real submissions
export function getStepProgress(
  step: AssetCompliancePath,
  submissions: AuthoritySubmission[],
): { progress: number; status: StepStatus } {
  const matchingSubmissions = submissions.filter(
    (s) => s.submission_type === step.submission_type,
  )

  if (matchingSubmissions.length === 0) {
    return { progress: 0, status: 'pending' }
  }

  const approved = matchingSubmissions.find((s) => s.status === 'APPROVED')
  if (approved) {
    return { progress: 100, status: 'completed' }
  }

  const rejected = matchingSubmissions.find((s) => s.status === 'REJECTED')
  if (rejected) {
    return { progress: 0, status: 'delayed' }
  }

  const inProgress = matchingSubmissions.find((s) =>
    ['SUBMITTED', 'IN_REVIEW', 'RFI'].includes(s.status),
  )
  if (inProgress) {
    if (inProgress.status === 'RFI')
      return { progress: 75, status: 'in_progress' }
    if (inProgress.status === 'IN_REVIEW')
      return { progress: 50, status: 'in_progress' }
    return { progress: 25, status: 'in_progress' }
  }

  const draft = matchingSubmissions.find((s) => s.status === 'DRAFT')
  if (draft) {
    return { progress: 10, status: 'in_progress' }
  }

  return { progress: 0, status: 'pending' }
}

type ComplianceStepDraft = Omit<
  AssetCompliancePath,
  'asset_type' | 'agency_id' | 'sequence_order' | 'created_at'
>

// Mock data generator for demonstration
export function getMockCompliancePaths(
  assetType: AssetType,
): AssetCompliancePath[] {
  const baseSteps: ComplianceStepDraft[] = [
    {
      id: '1',
      submission_type: 'planning_permission' as const,
      typical_duration_days: 21,
      is_mandatory: true,
    },
    {
      id: '2',
      submission_type: 'development_control' as const,
      typical_duration_days: 14,
      is_mandatory: true,
    },
    {
      id: '3',
      submission_type: 'building_plan' as const,
      typical_duration_days: 28,
      is_mandatory: true,
    },
    {
      id: '4',
      submission_type: 'structural_plan' as const,
      typical_duration_days: 21,
      is_mandatory: true,
    },
    {
      id: '5',
      submission_type: 'fire_safety' as const,
      typical_duration_days: 14,
      is_mandatory: true,
    },
    {
      id: '6',
      submission_type: 'environmental' as const,
      typical_duration_days: 14,
      is_mandatory: assetType === 'industrial',
    },
  ]

  if (assetType === 'heritage') {
    baseSteps.splice(1, 0, {
      id: '1b',
      submission_type: 'heritage_conservation' as const,
      typical_duration_days: 35,
      is_mandatory: true,
    })
  }

  baseSteps.push(
    {
      id: '7',
      submission_type: 'csc_application' as const,
      typical_duration_days: 7,
      is_mandatory: true,
    },
    {
      id: '8',
      submission_type: 'top_application' as const,
      typical_duration_days: 14,
      is_mandatory: true,
    },
  )

  return baseSteps.map((step, index) => ({
    ...step,
    asset_type: assetType,
    agency_id: 'mock-agency-id',
    sequence_order: index + 1,
    created_at: new Date().toISOString(),
  }))
}
