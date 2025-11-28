export function formatDuration(seconds: number | null, fallback: string): string {
  if (seconds === null || Number.isNaN(seconds)) {
    return fallback
  }
  if (seconds < 60) {
    return `${Math.round(seconds)}s`
  }
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) {
    return `${minutes}m`
  }
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  if (hours < 24) {
    return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`
  }
  const days = Math.floor(hours / 24)
  const remainingHours = hours % 24
  return remainingHours > 0 ? `${days}d ${remainingHours}h` : `${days}d`
}

export function formatDate(value: string, locale: string): string {
  if (!value) {
    return ''
  }
  try {
    const formatter = new Intl.DateTimeFormat(locale, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
    return formatter.format(new Date(value))
  } catch (error) {
    console.warn('Failed to format date', error)
    return value
  }
}

export function formatCurrency(
  value: number | null,
  currency: string,
  locale: string,
  fallback: string,
): string {
  if (value === null || Number.isNaN(value)) {
    return fallback
  }
  try {
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency,
      maximumFractionDigits: 0,
    }).format(value)
  } catch (error) {
    console.warn('Failed to format currency', error)
    return `${currency} ${value.toLocaleString(locale)}`
  }
}

export function formatShortCurrency(
  value: number | null,
  currency: string,
  locale: string,
): string {
  if (value === null || Number.isNaN(value)) {
    return ''
  }
  const abs = Math.abs(value)
  const suffix =
    abs >= 1_000_000_000
      ? { divisor: 1_000_000_000, label: 'B' }
      : abs >= 1_000_000
        ? { divisor: 1_000_000, label: 'M' }
        : abs >= 1_000
          ? { divisor: 1_000, label: 'K' }
          : null

  if (!suffix) {
    return formatCurrency(value, currency, locale, '')
  }
  const scaled = value / suffix.divisor
  try {
    const formatted = new Intl.NumberFormat(locale, {
      maximumFractionDigits: 1,
    }).format(scaled)
    return `${formatted}${suffix.label}`
  } catch (error) {
    console.warn('Failed to format short currency', error)
    return `${(Math.round(scaled * 10) / 10).toString()}${suffix.label}`
  }
}

export function formatPercent(
  value: number | null,
  fallback: string,
  fractionDigits = 1,
): string {
  if (value === null || Number.isNaN(value)) {
    return fallback
  }
  const percentValue = Math.abs(value) <= 1 ? value * 100 : value
  return `${percentValue.toFixed(fractionDigits)}%`
}

export function formatDays(value: number | null, fallback: string): string {
  if (value === null || Number.isNaN(value)) {
    return fallback
  }
  return `${value.toFixed(0)}d`
}

export function formatPercentagePointDelta(delta: number | null): string {
  if (delta === null || Number.isNaN(delta)) {
    return ''
  }
  const sign = delta > 0 ? '+' : ''
  return `${sign}${delta.toFixed(1)} pts`
}

export function formatDayDelta(delta: number | null): string {
  if (delta === null || Number.isNaN(delta)) {
    return ''
  }
  const sign = delta > 0 ? '+' : ''
  return `${sign}${delta.toFixed(0)}d`
}

export function formatCurrencyDelta(
  delta: number | null,
  currency: string,
  locale: string,
): string {
  if (delta === null || Number.isNaN(delta)) {
    return ''
  }
  const sign = delta > 0 ? '+' : delta < 0 ? '-' : ''
  const magnitude = Math.abs(delta)
  try {
    const formatted = new Intl.NumberFormat(locale, {
      style: 'currency',
      currency,
      maximumFractionDigits: 0,
    }).format(magnitude)
    return `${sign}${formatted}`
  } catch (error) {
    console.warn('Failed to format currency delta', error)
    const fallback = magnitude.toLocaleString(locale, {
      maximumFractionDigits: 0,
    })
    return `${sign}${currency} ${fallback}`
  }
}

export function toPercentValue(value: number | null): number | null {
  if (value === null || Number.isNaN(value)) {
    return null
  }
  return Math.abs(value) <= 1 ? value * 100 : value
}

export function isAbortError(
  error: unknown,
  controller?: AbortController,
): boolean {
  if (controller?.signal.aborted) {
    return true
  }
  if (error && typeof error === 'object' && 'name' in error) {
    return (error as { name?: unknown }).name === 'AbortError'
  }
  return false
}
