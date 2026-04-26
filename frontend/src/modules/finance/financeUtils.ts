const IN_PROGRESS_STATUSES = new Set([
  'queued',
  'started',
  'in_progress',
  'processing',
])

export const POLL_INTERVAL_MS = 5000
export const ALLOWED_FINANCE_ROLES = new Set(['developer', 'reviewer', 'admin'])

export const DEFAULT_SENSITIVITY_HEADERS = [
  'parameter',
  'scenario',
  'delta_label',
  'delta_value',
  'npv',
  'irr',
  'escalated_cost',
  'total_interest',
]

export function shortenProjectId(value: string): string {
  if (!value) {
    return ''
  }
  if (value.length <= 12) {
    return value
  }
  return `${value.slice(0, 6)}…${value.slice(-4)}`
}

export function isJobPending(status?: string | null): boolean {
  if (!status) {
    return false
  }
  const key = status.toLowerCase()
  if (IN_PROGRESS_STATUSES.has(key)) {
    return true
  }
  return key !== 'completed' && key !== 'success' && key !== 'failed'
}

export function escapeCsvValue(
  value: string | number | null | undefined,
): string {
  if (value == null) {
    return ''
  }
  const text = String(value)
  const needsQuote = /[",\n]/.test(text)
  if (!needsQuote) {
    return text
  }
  return `"${text.replace(/"/g, '""')}"`
}

export function downloadFile(
  content: string,
  filename: string,
  mime: string,
): void {
  if (typeof window === 'undefined') {
    return
  }
  const blob = new Blob([content], { type: mime })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.style.display = 'none'
  document.body.appendChild(anchor)
  anchor.click()
  document.body.removeChild(anchor)
  URL.revokeObjectURL(url)
}
