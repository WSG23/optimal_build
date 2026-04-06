export type FormState = {
  projectName: string
  address: string
  landUse: string
  zoneCode: string
  siteAreaSqm: string
  allowablePlotRatio: string
  currentGfaSqm: string
  targetGrossFloorAreaSqm: string
  buildingHeightMeters: string
  equityPct: string
  debtPct: string
  annualInterestRatePct: string
  discountRatePct: string
  exitCapRatePct: string
  saleCostPct: string
  holdYears: string
}

export const INITIAL_FORM_STATE: FormState = {
  projectName: 'Singapore quick screen',
  address: '1 Marina Boulevard, Singapore',
  landUse: 'residential',
  zoneCode: 'R',
  siteAreaSqm: '5000',
  allowablePlotRatio: '3.5',
  currentGfaSqm: '9000',
  targetGrossFloorAreaSqm: '14000',
  buildingHeightMeters: '45',
  equityPct: '40',
  debtPct: '60',
  annualInterestRatePct: '4.8',
  discountRatePct: '8',
  exitCapRatePct: '4',
  saleCostPct: '2',
  holdYears: '3',
}
