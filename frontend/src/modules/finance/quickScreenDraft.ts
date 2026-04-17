import type { FinanceScenarioInput } from '../../api/finance'
import type { RuleCorpusStatus } from '../../api/dealCalculator'

const STORAGE_KEY = 'ob:finance:quick-screen-draft'

export interface QuickScreenDraftAssessment {
  generatedAt: string
  ruleCorpusStatus?: RuleCorpusStatus | null
  sourceNotes: string[]
  recommendedRuleIds: string[]
}

export interface QuickScreenFinanceDraft {
  createdAt: string
  projectName?: string | null
  scenario: FinanceScenarioInput
  assessment?: QuickScreenDraftAssessment | null
}

function formatCoverageSummary(
  assessment: QuickScreenDraftAssessment | null | undefined,
): string | null {
  const status = assessment?.ruleCorpusStatus
  if (!status) {
    return null
  }
  const approved = status.counts.approved
  const applicable = status.counts.applicable
  return `Rule corpus: ${status.coverageState} (${status.confidence} confidence, ${approved}/${applicable} approved).`
}

export function buildQuickScreenAssessmentSummary(
  assessment: QuickScreenDraftAssessment | null | undefined,
): string[] {
  if (!assessment) {
    return []
  }
  const lines: string[] = []
  const coverage = formatCoverageSummary(assessment)
  if (coverage) {
    lines.push(coverage)
  }
  if (assessment.recommendedRuleIds.length > 0) {
    lines.push(
      `Recommended rules: ${assessment.recommendedRuleIds.join(', ')}.`,
    )
  }
  if (assessment.sourceNotes.length > 0) {
    lines.push(...assessment.sourceNotes.map((note) => `Source note: ${note}`))
  }
  return lines
}

export function buildQuickScreenScenarioDescription(
  description: string | undefined,
  assessment: QuickScreenDraftAssessment | null | undefined,
): string | undefined {
  const parts: string[] = []
  const trimmedDescription = description?.trim()
  if (trimmedDescription) {
    parts.push(trimmedDescription)
  }
  const assessmentLines = buildQuickScreenAssessmentSummary(assessment)
  if (assessmentLines.length > 0) {
    parts.push('[Quick screen context]')
    parts.push(...assessmentLines)
  }
  return parts.length > 0 ? parts.join('\n') : undefined
}

export function saveQuickScreenFinanceDraft(
  draft: QuickScreenFinanceDraft,
): void {
  if (typeof window === 'undefined') {
    return
  }
  window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(draft))
}

export function readQuickScreenFinanceDraft(): QuickScreenFinanceDraft | null {
  if (typeof window === 'undefined') {
    return null
  }
  const raw = window.sessionStorage.getItem(STORAGE_KEY)
  if (!raw) {
    return null
  }
  try {
    const parsed = JSON.parse(raw) as QuickScreenFinanceDraft
    if (!parsed?.scenario?.name) {
      return null
    }
    return parsed
  } catch {
    return null
  }
}

export function clearQuickScreenFinanceDraft(): void {
  if (typeof window === 'undefined') {
    return
  }
  window.sessionStorage.removeItem(STORAGE_KEY)
}
