export type DetectionStatus = 'source' | 'pending' | 'approved' | 'rejected'

export interface DetectedUnit {
  id: string
  floor: number
  unitLabel: string
  areaSqm: number
  status: DetectionStatus
}

export interface RoiMetrics {
  automationScore: number
  savingsPercent: number
  reviewHoursSaved: number
  paybackWeeks: number
}
