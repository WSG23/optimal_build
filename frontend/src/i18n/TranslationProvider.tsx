import type { ReactNode } from 'react'

import i18n from './i18n'
import { I18nContext } from './context'

export function TranslationProvider({ children }: { children: ReactNode }) {
  return <I18nContext.Provider value={i18n}>{children}</I18nContext.Provider>
}
