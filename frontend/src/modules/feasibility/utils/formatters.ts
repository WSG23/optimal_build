import { cssVar } from '../../../tokens'

export function formatFileSize(bytes: number | null, locale: string): string {
  if (bytes == null || Number.isNaN(bytes)) {
    return '—'
  }
  if (bytes < 1024) {
    return `${new Intl.NumberFormat(locale).format(bytes)} B`
  }
  const units = ['KB', 'MB', 'GB'] as const
  let value = bytes / 1024
  let index = 0
  while (value >= 1024 && index < units.length - 1) {
    value /= 1024
    index += 1
  }
  return `${new Intl.NumberFormat(locale, { maximumFractionDigits: 1 }).format(value)} ${units[index]}`
}

export function anonymiseAddress(address: string): string {
  const trimmed = address.trim()
  if (!trimmed) {
    return ''
  }
  if (trimmed.length <= 5) {
    return `${trimmed[0]}***`
  }
  const prefix = trimmed.slice(0, 3)
  const suffix = trimmed.slice(-2)
  return `${prefix}…${suffix}`
}

export function readCssVar(token: string): string {
  return String((cssVar as (name: string) => unknown)(token))
}

export function createNumberFormatter(
  locale: string,
  maxFractionDigits = 0,
): Intl.NumberFormat {
  return new Intl.NumberFormat(locale, {
    maximumFractionDigits: maxFractionDigits,
  })
}

export function createDecimalFormatter(locale: string): Intl.NumberFormat {
  return new Intl.NumberFormat(locale, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}
