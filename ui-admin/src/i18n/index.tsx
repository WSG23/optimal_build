import type { ReactNode } from 'react'
import { createContext, useContext, useMemo } from 'react'

import en from './locales/en.json'
import ja from './locales/ja.json'

type Locale = 'en' | 'ja'

type TranslationRecord = Record<string, unknown>

type TranslationContextValue = {
  locale: Locale
  t: (key: string) => string
}

const RESOURCES: Record<Locale, TranslationRecord> = {
  en,
  ja,
}

const TranslationContext = createContext<TranslationContextValue>({
  locale: 'en',
  t: (key) => resolveTranslation('en', key),
})

function resolveTranslation(locale: Locale, key: string): string {
  const segments = key.split('.')
  let node: unknown = RESOURCES[locale]

  for (const segment of segments) {
    if (typeof node !== 'object' || node === null) {
      return key
    }
    node = (node as TranslationRecord)[segment]
  }

  return typeof node === 'string' ? node : key
}

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

export function useTranslation(): TranslationContextValue {
  return useContext(TranslationContext)
}
