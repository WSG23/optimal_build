import { createContext } from 'react'

import en from './locales/en.json'
import ja from './locales/ja.json'

export type Locale = 'en' | 'ja'

type TranslationRecord = Record<string, unknown>

export type TranslationContextValue = {
  locale: Locale
  t: (key: string) => string
}

export const RESOURCES: Record<Locale, TranslationRecord> = {
  en,
  ja,
}

export function resolveTranslation(locale: Locale, key: string): string {
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

export const TranslationContext = createContext<TranslationContextValue>({
  locale: 'en',
  t: (key) => resolveTranslation('en', key),
})
