import { useContext } from 'react'
import { DeveloperContext } from './developerContextDef'

export function useDeveloperMode() {
  const context = useContext(DeveloperContext)
  if (context === undefined) {
    return {
      isDeveloperMode: false,
      toggleDeveloperMode: () => {},
    }
  }
  return context
}
