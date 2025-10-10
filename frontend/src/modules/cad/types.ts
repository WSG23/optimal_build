export type DetectionStatus = 'source' | 'pending' | 'approved' | 'rejected'

export interface DetectedUnit {
  id: string
  floor: number
  unitLabel: string
  areaSqm: number
  status: DetectionStatus
  severity?: 'high' | 'medium' | 'low' | 'none'
  missingMetricKey?: string
  overrideValue?: number | null
  overrideDisplay?: string
  metricLabel?: string
}

export interface RoiMetrics {
  automationScore: number
  savingsPercent: number
  reviewHoursSaved: number
  paybackWeeks: number
}
