import type { ChangeEvent } from 'react'
import { useCallback, useState } from 'react'

import type { FinancialAssumptions } from '../types'
import { DEFAULT_ASSUMPTIONS } from '../types'

export interface UseFinancialsResult {
  financialInputs: FinancialAssumptions
  financialErrors: Partial<Record<keyof FinancialAssumptions, string>>
  appliedFinancials: {
    capRatePercent: number
    interestRatePercent: number
    targetMarginPercent: number
  }
  handleFinancialChange: (
    key: keyof FinancialAssumptions,
  ) => (event: ChangeEvent<HTMLInputElement>) => void
}

export function useFinancials(): UseFinancialsResult {
  const [financialInputs, setFinancialInputs] = useState<FinancialAssumptions>({
    capRatePercent: DEFAULT_ASSUMPTIONS.capRatePercent.toString(),
    interestRatePercent: DEFAULT_ASSUMPTIONS.interestRatePercent.toString(),
    targetMarginPercent: DEFAULT_ASSUMPTIONS.targetMarginPercent.toString(),
  })

  const [financialErrors, setFinancialErrors] = useState<
    Partial<Record<keyof FinancialAssumptions, string>>
  >({})

  const [appliedFinancials, setAppliedFinancials] = useState({
    capRatePercent: DEFAULT_ASSUMPTIONS.capRatePercent,
    interestRatePercent: DEFAULT_ASSUMPTIONS.interestRatePercent,
    targetMarginPercent: DEFAULT_ASSUMPTIONS.targetMarginPercent,
  })

  const handleFinancialChange = useCallback(
    (key: keyof FinancialAssumptions) =>
      (event: ChangeEvent<HTMLInputElement>) => {
        const value = event.target.value
        setFinancialInputs((prev) => ({ ...prev, [key]: value }))
        setFinancialErrors((prev) => ({ ...prev, [key]: undefined }))

        if (!value.trim()) {
          // Allow empty string while typing, but don't apply it
          return
        }

        const numeric = parseFloat(value)
        if (isNaN(numeric) || numeric < 0) {
          setFinancialErrors((prev) => ({ ...prev, [key]: 'Invalid number' }))
          return
        }

        setAppliedFinancials((prev) => ({
          ...prev,
          [key]: numeric,
        }))
      },
    [],
  )

  return {
    financialInputs,
    financialErrors,
    appliedFinancials,
    handleFinancialChange,
  }
}
