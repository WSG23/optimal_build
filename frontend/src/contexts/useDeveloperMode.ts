import { useContext } from 'react'
import { DeveloperContext } from './developerContextDef'

export function useDeveloperMode() {
  const context = useContext(DeveloperContext)
  if (context === undefined) {
    throw new Error('useDeveloperMode must be used within a DeveloperProvider')
  }
  return context
}
