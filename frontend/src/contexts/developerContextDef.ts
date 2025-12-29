import { createContext } from 'react'

interface DeveloperContextType {
  isDeveloperMode: boolean
  toggleDeveloperMode: () => void
}

export const DeveloperContext = createContext<DeveloperContextType | undefined>(
  undefined,
)
