import { useContext } from 'react'

import { TranslationContext, type TranslationContextValue } from './context'

export const useTranslation = (): TranslationContextValue =>
  useContext(TranslationContext)
