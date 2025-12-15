import { createContext, useContext } from 'react'

interface BaseLayoutContextValue {
  inBaseLayout: boolean
  topOffset: number
}

const BaseLayoutContext = createContext<BaseLayoutContextValue>({
  inBaseLayout: false,
  topOffset: 0,
})

export function useBaseLayoutContext() {
  return useContext(BaseLayoutContext)
}

export const BaseLayoutProvider = BaseLayoutContext.Provider
