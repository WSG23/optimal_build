/**
 * Chart Theme Utilities for Finance Module
 *
 * Centralized chart styling that follows UI_STANDARDS.md:
 * - Use Recharts only
 * - Colors from theme palette (dark mode compatible)
 * - Bar radius matches --ob-radius-sm
 * - Axis lines disabled for minimal aesthetic
 */

import { Theme, alpha } from '@mui/material'

/**
 * Returns chart colors derived from the MUI theme.
 * Use these instead of hardcoded hex colors to support dark mode.
 */
export function getChartColors(theme: Theme) {
  return {
    // Capital stack colors
    equity: theme.palette.success.main,
    seniorDebt: theme.palette.primary.main,
    mezzanine: theme.palette.secondary.main,
    bridge: theme.palette.warning.main,
    other: theme.palette.grey[500],

    // Chart structural colors
    grid: alpha(theme.palette.divider, 0.3),
    gridDashed: alpha(theme.palette.divider, 0.4),
    axisText: theme.palette.text.secondary,
    tooltipBg: theme.palette.background.paper,
    tooltipBorder: theme.palette.divider,

    // Line chart colors
    line: theme.palette.text.primary,
    lineDot: theme.palette.text.primary,
    lineArea: alpha(theme.palette.primary.main, 0.1),
  }
}

/**
 * Chart radius values that match design tokens.
 * Per UI_STANDARDS.md: bar corners use radius 4 (--ob-radius-sm)
 */
export const chartRadii = {
  /** Bar corner radius - matches --ob-radius-sm */
  bar: 4,
  /** Tooltip border radius - matches --ob-radius-sm */
  tooltip: 4,
} as const

/**
 * Chart sizing constants from design tokens.
 */
export const chartSizes = {
  /** Default bar width for bar charts */
  barSize: 60,
  /** Narrow bar width for dense charts */
  barSizeNarrow: 40,
  /** Wide bar width for sparse charts */
  barSizeWide: 80,
  /** Line stroke width */
  lineStrokeWidth: 2,
  /** Line dot radius */
  lineDotRadius: 3,
  /** Axis tick font size */
  axisFontSize: 12,
  /** Legend padding top */
  legendPaddingTop: 20,
} as const

/**
 * Common axis props for Recharts XAxis/YAxis.
 * Per UI_STANDARDS.md: axisLine={false}, tickLine={false}
 */
export function getAxisProps(theme: Theme) {
  return {
    axisLine: false,
    tickLine: false,
    tick: {
      fill: theme.palette.text.secondary,
      fontSize: chartSizes.axisFontSize,
    },
  }
}

/**
 * Common CartesianGrid props.
 * Per UI_STANDARDS.md: vertical={false}, stroke from theme
 */
export function getGridProps(theme: Theme) {
  return {
    stroke: alpha(theme.palette.divider, 0.3),
    vertical: false,
  }
}

/**
 * Common Tooltip content style.
 * Per UI_STANDARDS.md: borderRadius 4 (--ob-radius-sm)
 */
export function getTooltipStyle(theme: Theme) {
  return {
    borderRadius: chartRadii.tooltip,
    border: 'none',
    boxShadow: theme.shadows[2],
    backgroundColor: theme.palette.background.paper,
    padding: 'var(--ob-space-075)',
  }
}

/**
 * Bar radius for stacked bars.
 * Returns [topLeft, topRight, bottomRight, bottomLeft]
 */
export function getBarRadius(
  position: 'top' | 'bottom' | 'middle',
): [number, number, number, number] {
  const r = chartRadii.bar
  switch (position) {
    case 'top':
      return [r, r, 0, 0]
    case 'bottom':
      return [0, 0, r, r]
    case 'middle':
    default:
      return [0, 0, 0, 0]
  }
}

/**
 * Format currency for chart tooltips and axis labels.
 */
export function formatCurrencyShort(
  value: number,
  currency = 'SGD',
  _locale = 'en-SG',
): string {
  const absValue = Math.abs(value)
  let formatted: string
  let suffix: string

  if (absValue >= 1_000_000_000) {
    formatted = (value / 1_000_000_000).toFixed(1)
    suffix = 'B'
  } else if (absValue >= 1_000_000) {
    formatted = (value / 1_000_000).toFixed(1)
    suffix = 'M'
  } else if (absValue >= 1_000) {
    formatted = (value / 1_000).toFixed(0)
    suffix = 'k'
  } else {
    formatted = value.toFixed(0)
    suffix = ''
  }

  // Remove trailing .0
  formatted = formatted.replace(/\.0$/, '')

  const currencySymbol = currency === 'SGD' ? '$' : currency
  return `${currencySymbol}${formatted}${suffix}`
}

/**
 * Format currency for detailed display (tooltips, tables).
 */
export function formatCurrencyFull(
  value: number,
  currency = 'SGD',
  locale = 'en-SG',
): string {
  try {
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency,
      maximumFractionDigits: 0,
    }).format(value)
  } catch {
    return `${currency} ${value.toLocaleString(locale)}`
  }
}

/**
 * Format percentage for chart display.
 */
export function formatPercent(value: number, decimals = 1): string {
  return `${(value * 100).toFixed(decimals)}%`
}
