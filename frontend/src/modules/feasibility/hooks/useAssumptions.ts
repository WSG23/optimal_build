import type { ChangeEvent } from 'react'
import { useCallback, useEffect, useState } from 'react'

import type { AssumptionInputs, AssumptionErrors } from '../types'
import { DEFAULT_ASSUMPTIONS } from '../types'
import { getEngineeringDefaults, type EngineeringDefaults } from '../../../api/feasibility'

interface UseAssumptionsResult {
  assumptionInputs: AssumptionInputs
  assumptionErrors: AssumptionErrors
  appliedAssumptions: { typFloorToFloorM: number; efficiencyRatio: number }
  handleAssumptionChange: (
    key: keyof AssumptionInputs,
  ) => (event: ChangeEvent<HTMLInputElement>) => void
  handleResetAssumptions: () => void
}

export function useAssumptions(): UseAssumptionsResult {
  const [assumptionInputs, setAssumptionInputs] = useState<AssumptionInputs>(
    () => ({
      typFloorToFloorM: DEFAULT_ASSUMPTIONS.typFloorToFloorM.toString(),
      efficiencyRatio: DEFAULT_ASSUMPTIONS.efficiencyRatio.toString(),
    }),
  )
  const [assumptionErrors, setAssumptionErrors] = useState<AssumptionErrors>({})
  const [appliedAssumptions, setAppliedAssumptions] = useState<{
    typFloorToFloorM: number
    efficiencyRatio: number
  }>({
    ...DEFAULT_ASSUMPTIONS,
  })

  useEffect(() => {
    const controller = new AbortController()
    getEngineeringDefaults(controller.signal)
      .then((defaults: EngineeringDefaults) => {
        if (!defaults || typeof defaults.typFloorToFloorM !== 'number') {
           console.warn('Invalid defaults received:', defaults)
           return
        }
        setAssumptionInputs({
          typFloorToFloorM: (defaults.typFloorToFloorM || DEFAULT_ASSUMPTIONS.typFloorToFloorM).toString(),
          efficiencyRatio: (defaults.efficiencyRatio || DEFAULT_ASSUMPTIONS.efficiencyRatio).toString(),
        })
        setAppliedAssumptions({
          typFloorToFloorM: defaults.typFloorToFloorM || DEFAULT_ASSUMPTIONS.typFloorToFloorM,
          efficiencyRatio: defaults.efficiencyRatio || DEFAULT_ASSUMPTIONS.efficiencyRatio,
        })
      })
      .catch((err: unknown) => {
        console.warn('Failed to load engineering defaults', err)
      })
    return () => controller.abort()
  }, [])

  const handleAssumptionChange = useCallback(
    (key: keyof AssumptionInputs) => (event: ChangeEvent<HTMLInputElement>) => {
      const value = event.target.value
      setAssumptionInputs((previous) => ({ ...previous, [key]: value }))
      setAssumptionErrors((previous) => ({ ...previous, [key]: undefined }))

      if (!value.trim()) {
        setAssumptionErrors((previous) => ({ ...previous, [key]: 'required' }))
        return
      }

      const numeric = Number.parseFloat(value)
      if (!Number.isFinite(numeric) || numeric <= 0) {
        setAssumptionErrors((previous) => ({ ...previous, [key]: 'invalid' }))
        return
      }

      if (key === 'efficiencyRatio' && (numeric <= 0 || numeric > 1)) {
        setAssumptionErrors((previous) => ({ ...previous, [key]: 'range' }))
        return
      }

      setAppliedAssumptions((previous) => {
        if (previous[key] === numeric) {
          return previous
        }
        return {
          ...previous,
          [key]: numeric,
        }
      })
    },
    [],
  )

  const handleResetAssumptions = useCallback(() => {
    setAssumptionInputs({
      typFloorToFloorM: DEFAULT_ASSUMPTIONS.typFloorToFloorM.toString(),
      efficiencyRatio: DEFAULT_ASSUMPTIONS.efficiencyRatio.toString(),
    })
    setAssumptionErrors({})
    setAppliedAssumptions({ ...DEFAULT_ASSUMPTIONS })
  }, [])

  return {
    assumptionInputs,
    assumptionErrors,
    appliedAssumptions,
    handleAssumptionChange,
    handleResetAssumptions,
  }
}
