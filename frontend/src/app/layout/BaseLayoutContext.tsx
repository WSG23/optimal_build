import { createContext, useContext } from 'react'

interface BaseLayoutContextValue {
  inBaseLayout: boolean
}

const BaseLayoutContext = createContext<BaseLayoutContextValue>({
  inBaseLayout: false,
})

export function useBaseLayoutContext() {
  return useContext(BaseLayoutContext)
}

export const BaseLayoutProvider = BaseLayoutContext.Provider
