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
