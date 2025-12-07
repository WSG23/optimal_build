import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react'

interface DeveloperContextType {
  isDeveloperMode: boolean
  toggleDeveloperMode: () => void
}

const DeveloperContext = createContext<DeveloperContextType | undefined>(
  undefined,
)

export function DeveloperProvider({ children }: { children: ReactNode }) {
  const [isDeveloperMode, setIsDeveloperMode] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false
    return localStorage.getItem('optimal_build_dev_mode') === 'true'
  })

  useEffect(() => {
    localStorage.setItem('optimal_build_dev_mode', String(isDeveloperMode))
  }, [isDeveloperMode])

  const toggleDeveloperMode = () => {
    setIsDeveloperMode((prev) => !prev)
  }

  return (
    <DeveloperContext.Provider value={{ isDeveloperMode, toggleDeveloperMode }}>
      {children}
    </DeveloperContext.Provider>
  )
}

export function useDeveloperMode() {
  const context = useContext(DeveloperContext)
  if (context === undefined) {
    throw new Error('useDeveloperMode must be used within a DeveloperProvider')
  }
  return context
}
