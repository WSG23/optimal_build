import type { ReactNode } from 'react'
import { useMemo } from 'react'

import {
  TranslationContext,
  resolveTranslation,
  type Locale,
  type TranslationContextValue,
} from './context'

export function TranslationProvider({
  locale = 'en',
  children,
}: {
  locale?: Locale
  children: ReactNode
}) {
  const value = useMemo<TranslationContextValue>(
    () => ({
      locale,
      t: (key: string) => resolveTranslation(locale, key),
    }),
    [locale],
  )

  return (
    <TranslationContext.Provider value={value}>
      {children}
    </TranslationContext.Provider>
  )
}
