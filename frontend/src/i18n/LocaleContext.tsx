/* eslint-disable react-refresh/only-export-components */
import { createContext, ReactNode, useContext, useMemo, useState } from 'react'

import { STRINGS, type AppStrings, type Locale } from './strings'

interface LocaleContextValue {
  locale: Locale
  strings: AppStrings
  setLocale: (locale: Locale) => void
}

const LocaleContext = createContext<LocaleContextValue | undefined>(undefined)

interface LocaleProviderProps {
  children: ReactNode
  defaultLocale?: Locale
}

export function LocaleProvider({ children, defaultLocale = 'en' }: LocaleProviderProps) {
  const [locale, setLocale] = useState<Locale>(defaultLocale)

  const value = useMemo<LocaleContextValue>(
    () => ({
      locale,
      strings: STRINGS[locale],
      setLocale,
    }),
    [locale],
  )

  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>
}

export function useLocale() {
  const context = useContext(LocaleContext)
  if (!context) {
    throw new Error('useLocale must be used within a LocaleProvider')
  }
  return context
}
