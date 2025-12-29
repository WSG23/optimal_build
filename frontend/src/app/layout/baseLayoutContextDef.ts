import { createContext } from 'react'

interface BaseLayoutContextValue {
  inBaseLayout: boolean
  topOffset: number | string
}

export const BaseLayoutContext = createContext<BaseLayoutContextValue>({
  inBaseLayout: false,
  topOffset: 0,
})
