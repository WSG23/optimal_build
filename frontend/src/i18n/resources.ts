import en from './locales/en.json'
import ja from './locales/ja.json'

export const resources = {
  en: { translation: en },
  ja: { translation: ja },
} as const

export const supportedLanguages = [
  {
    value: 'en',
    labelKey: 'common.language.options.en',
    menuCode: 'EN',
    nativeLabel: 'English',
  },
  {
    value: 'ja',
    labelKey: 'common.language.options.ja',
    menuCode: 'JA',
    nativeLabel: '日本語',
  },
] as const

export type SupportedLanguage = (typeof supportedLanguages)[number]['value']
export type SupportedLanguageOption = (typeof supportedLanguages)[number]

export function getSupportedLanguage(
  language: string,
): SupportedLanguageOption {
  return (
    supportedLanguages.find((option) => option.value === language) ??
    supportedLanguages[0]
  )
}
