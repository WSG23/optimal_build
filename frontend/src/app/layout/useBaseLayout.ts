import { useContext } from 'react'
import { BaseLayoutContext } from './baseLayoutContextDef'

export function useBaseLayoutContext() {
  return useContext(BaseLayoutContext)
}
