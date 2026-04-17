import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { DeveloperContext } from './developerContextDef'

export { DeveloperContext }

export function DeveloperProvider({ children }: { children: ReactNode }) {
  const [isDeveloperMode, setIsDeveloperMode] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false
    return localStorage.getItem('optimal_build_dev_mode') === 'true'
  })

  useEffect(() => {
    localStorage.setItem('optimal_build_dev_mode', String(isDeveloperMode))
  }, [isDeveloperMode])

  const toggleDeveloperMode = useCallback(() => {
    setIsDeveloperMode((prev) => !prev)
  }, [])

  const contextValue = useMemo(
    () => ({ isDeveloperMode, toggleDeveloperMode }),
    [isDeveloperMode, toggleDeveloperMode],
  )

  return (
    <DeveloperContext.Provider value={contextValue}>
      {children}
    </DeveloperContext.Provider>
  )
}
