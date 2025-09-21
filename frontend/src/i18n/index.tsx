import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import en from './locales/en.json'
import ja from './locales/ja.json'

export const resources = {
  en: { translation: en },
  ja: { translation: ja },
} as const

export const supportedLanguages = [
  { value: 'en', labelKey: 'common.language.options.en' },
  { value: 'ja', labelKey: 'common.language.options.ja' },
] as const

export type SupportedLanguage = (typeof supportedLanguages)[number]['value']

interface TranslationOptions {
  ns?: string
  defaultValue?: string
  returnObjects?: boolean
  [key: string]: unknown
}

type Listener = () => void

type ResourceDictionary = Record<string, Record<string, unknown>>

type Resources = Record<string, ResourceDictionary>

const STORAGE_KEY = 'optimal_build:locale'
const QUERY_KEYS = ['lang', 'locale', 'lng']

function isBrowser(): boolean {
  return typeof window !== 'undefined'
}

function parseQueryString(): URLSearchParams | null {
  if (!isBrowser()) {
    return null
  }
  try {
    return new URLSearchParams(window.location.search)
  } catch (error) {
    console.error('Unable to parse query string for locale detection', error)
    return null
  }
}

class I18n {
  private listeners: Set<Listener> = new Set()
  private resources: Resources
  private fallbackLng: SupportedLanguage
  private supported: SupportedLanguage[]
  private detectionOrder: string[]
  private storageKey: string

  language: string
  resolvedLanguage: SupportedLanguage

  constructor({
    resources,
    fallbackLng,
    supportedLngs,
    detectionOrder,
    storageKey,
  }: {
    resources: Resources
    fallbackLng: SupportedLanguage
    supportedLngs: SupportedLanguage[]
    detectionOrder: string[]
    storageKey: string
  }) {
    this.resources = resources
    this.fallbackLng = fallbackLng
    this.supported = supportedLngs
    this.detectionOrder = detectionOrder
    this.storageKey = storageKey
    this.language = fallbackLng
    this.resolvedLanguage = fallbackLng
    this.initialize()
  }

  private initialize() {
    const detected = this.detectLanguage()
    this.language = detected
    this.resolvedLanguage = this.isSupported(detected) ? (detected as SupportedLanguage) : this.fallbackLng
    this.persistLanguage(this.resolvedLanguage)
  }

  private detectLanguage(): string {
    for (const method of this.detectionOrder) {
      const detected = this.detectFrom(method)
      if (detected) {
        return detected
      }
    }
    return this.fallbackLng
  }

  private detectFrom(method: string): string | null {
    if (!isBrowser()) {
      return null
    }

    try {
      switch (method) {
        case 'localStorage':
          return window.localStorage.getItem(this.storageKey)
        case 'querystring': {
          const params = parseQueryString()
          if (!params) {
            return null
          }
          for (const key of QUERY_KEYS) {
            const value = params.get(key)
            if (value) {
              return value
            }
          }
          return null
        }
        case 'navigator':
          return window.navigator.language || null
        default:
          return null
      }
    } catch (error) {
      console.warn(`Locale detection via ${method} failed`, error)
      return null
    }
  }

  private isSupported(language: string): language is SupportedLanguage {
    return this.supported.includes(language as SupportedLanguage)
  }

  private persistLanguage(language: string) {
    if (!isBrowser()) {
      return
    }
    try {
      window.localStorage.setItem(this.storageKey, language)
    } catch (error) {
      console.warn('Unable to persist locale preference', error)
    }
  }

  async changeLanguage(language: string) {
    this.language = language
    this.resolvedLanguage = this.isSupported(language)
      ? (language as SupportedLanguage)
      : this.fallbackLng
    this.persistLanguage(this.resolvedLanguage)
    this.notify()
    return this
  }

  subscribe(listener: Listener) {
    this.listeners.add(listener)
    return () => {
      this.listeners.delete(listener)
    }
  }

  private notify() {
    for (const listener of this.listeners) {
      listener()
    }
  }

  private getResource(language: SupportedLanguage, namespace: string): Record<string, unknown> | null {
    const namespaces = this.resources[language]
    if (!namespaces) {
      return null
    }
    return namespaces[namespace] ?? null
  }

  private getValue(resource: Record<string, unknown> | null, key: string): unknown {
    if (!resource) {
      return undefined
    }
    const segments = key.split('.')
    let current: unknown = resource
    for (const segment of segments) {
      if (typeof current !== 'object' || current === null) {
        return undefined
      }
      current = (current as Record<string, unknown>)[segment]
    }
    return current
  }

  private interpolate(template: string, options: TranslationOptions): string {
    return template.replace(/\{\{\s*(.+?)\s*\}\}/g, (_, token: string) => {
      const key = token.trim()
      if (key in options && options[key] !== undefined && options[key] !== null) {
        return String(options[key])
      }
      return ''
    })
  }

  t(key: string, options: TranslationOptions = {}): any {
    const namespace = options.ns ?? 'translation'
    const languagesToCheck: SupportedLanguage[] = []
    if (this.resolvedLanguage) {
      languagesToCheck.push(this.resolvedLanguage)
    }
    if (!languagesToCheck.includes(this.fallbackLng)) {
      languagesToCheck.push(this.fallbackLng)
    }

    for (const language of languagesToCheck) {
      const resource = this.getResource(language, namespace)
      const rawValue = this.getValue(resource, key)
      if (rawValue !== undefined) {
        if (options.returnObjects && typeof rawValue !== 'string') {
          return rawValue
        }
        if (typeof rawValue === 'string') {
          return this.interpolate(rawValue, options)
        }
        return rawValue
      }
    }

    if (options.defaultValue !== undefined) {
      return options.defaultValue
    }

    return options.returnObjects ? null : key
  }
}

const detectionOrder = isBrowser()
  ? ['localStorage', 'querystring', 'navigator']
  : ['querystring']

const i18n = new I18n({
  resources: resources as Resources,
  fallbackLng: 'en',
  supportedLngs: supportedLanguages.map((item) => item.value),
  detectionOrder,
  storageKey: STORAGE_KEY,
})

const I18nContext = createContext<I18n>(i18n)

export function TranslationProvider({ children }: { children: ReactNode }) {
  return <I18nContext.Provider value={i18n}>{children}</I18nContext.Provider>
}

export function useTranslation() {
  const instance = useContext(I18nContext)
  const [, forceUpdate] = useState(0)

  useEffect(() => instance.subscribe(() => forceUpdate((value) => value + 1)), [instance])

  const translate = useCallback(
    (key: string, options?: TranslationOptions) => instance.t(key, options),
    [instance],
  )

  return useMemo(() => ({ t: translate, i18n: instance }), [instance, translate])
}

export const i18nReady = Promise.resolve(i18n)

declare global {
  interface Window {
    __APP_I18N__?: I18n
  }

  // eslint-disable-next-line no-var
  var __APP_I18N__: I18n | undefined
}

if (isBrowser()) {
  window.__APP_I18N__ = i18n
} else {
  globalThis.__APP_I18N__ = i18n
}

export default i18n
