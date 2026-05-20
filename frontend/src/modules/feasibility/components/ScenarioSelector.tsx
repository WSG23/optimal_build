import Business from '@mui/icons-material/Business'
import Foundation from '@mui/icons-material/Foundation'
import HomeWork from '@mui/icons-material/HomeWork'
import Landscape from '@mui/icons-material/Landscape'
import { Typography } from '@mui/material'
import { useEffect, useRef } from 'react'

import { logChoiceSet } from '../../../services/telemetry/decisions'
import type { ChoiceSetHandle } from '../../../services/telemetry/decisions'

interface ScenarioSelectorProps {
  value: string
  onChange: (value: string) => void
}

const OPTIONS = [
  {
    value: 'Mixed Use',
    label: 'Mixed Use',
    icon: <Business fontSize="small" />,
  },
  {
    value: 'Residential',
    label: 'Residential',
    icon: <HomeWork fontSize="small" />,
  },
  {
    value: 'Commercial',
    label: 'Commercial',
    icon: <Foundation fontSize="small" />,
  },
  {
    value: 'Raw Land',
    label: 'Raw Land',
    icon: <Landscape fontSize="small" />,
  },
] as const

export function ScenarioSelector({ value, onChange }: ScenarioSelectorProps) {
  // Log presentation once per mount so the dataset captures the full choice
  // set (including the options the user does NOT pick — that's the
  // preference-pair signal). `resolve` is called when a click commits a pick.
  const choiceSetRef = useRef<ChoiceSetHandle | null>(null)
  useEffect(() => {
    choiceSetRef.current = logChoiceSet({
      decisionType: 'feasibility_scenario_pick',
      alternatives: OPTIONS.map((opt, rank) => ({
        rank,
        label: opt.value,
      })),
    })
    return () => {
      // Component unmounted without a pick → record as dismissed.
      if (choiceSetRef.current) {
        void choiceSetRef.current.resolve({ dismissedReason: 'unmounted' })
        choiceSetRef.current = null
      }
    }
  }, [])

  const handlePick = (picked: string, rank: number) => {
    if (choiceSetRef.current) {
      void choiceSetRef.current.resolve({ chosenRank: rank })
      choiceSetRef.current = null
    }
    onChange(picked)
  }

  return (
    <div className="scenario-selector">
      {OPTIONS.map((option, rank) => {
        const isSelected = value === option.value
        return (
          <button
            key={option.value}
            type="button"
            onClick={() => handlePick(option.value, rank)}
            className={`scenario-selector__option ${isSelected ? 'scenario-selector__option--selected' : ''}`}
            aria-pressed={isSelected}
          >
            <span className="scenario-selector__icon">{option.icon}</span>

            <Typography variant="body2" className="scenario-selector__label">
              {option.label}
            </Typography>
          </button>
        )
      })}
    </div>
  )
}
