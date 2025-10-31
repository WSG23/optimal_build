import { useCallback, useReducer } from 'react'
import {
  generateProfessionalPack,
  type ProfessionalPackSummary,
  type ProfessionalPackType,
} from '../../../../api/agents'

interface MarketingPackState {
  packs: ProfessionalPackSummary[]
  isGenerating: boolean
  generatingType: ProfessionalPackType | null
  error: string | null
}

type Action =
  | { type: 'GENERATE_START'; packType: ProfessionalPackType }
  | {
      type: 'GENERATE_SUCCESS'
      payload: ProfessionalPackSummary
    }
  | { type: 'GENERATE_FAILURE'; error: string }
  | { type: 'CLEAR_ERROR' }

const initialState: MarketingPackState = {
  packs: [],
  isGenerating: false,
  generatingType: null,
  error: null,
}

function reducer(state: MarketingPackState, action: Action): MarketingPackState {
  switch (action.type) {
    case 'GENERATE_START':
      return {
        ...state,
        isGenerating: true,
        generatingType: action.packType,
        error: null,
      }
    case 'GENERATE_SUCCESS':
      return {
        ...state,
        isGenerating: false,
        generatingType: null,
        packs: [action.payload, ...state.packs],
      }
    case 'GENERATE_FAILURE':
      return {
        ...state,
        isGenerating: false,
        generatingType: null,
        error: action.error,
      }
    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null,
      }
    default:
      return state
  }
}

export function useMarketingPacks() {
  const [state, dispatch] = useReducer(reducer, initialState)

  const generatePack = useCallback(
    async (propertyId: string, packType: ProfessionalPackType) => {
      dispatch({ type: 'GENERATE_START', packType })
      try {
        const summary = await generateProfessionalPack(propertyId, packType)
        dispatch({ type: 'GENERATE_SUCCESS', payload: summary })
        return summary
      } catch (error) {
        const message =
          error instanceof Error ? error.message : 'Unable to generate pack.'
        dispatch({ type: 'GENERATE_FAILURE', error: message })
        throw error
      }
    },
    [],
  )

  const clearError = useCallback(() => {
    dispatch({ type: 'CLEAR_ERROR' })
  }, [])

  return {
    packs: state.packs,
    isGenerating: state.isGenerating,
    generatingType: state.generatingType,
    error: state.error,
    generatePack,
    clearError,
  }
}
