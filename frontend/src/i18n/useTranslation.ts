import { useCallback, useContext, useEffect, useMemo, useState } from 'react'

import type { TranslationOptions } from './i18n'
import i18n from './i18n'
import { I18nContext } from './context'

export function useTranslation() {
  let instance = i18n

  try {
    instance = useContext(I18nContext)
  } catch (error) {
    if (import.meta.env?.DEV) {
      console.warn('Translation context unavailable, using default instance instead.', error)
    }
  }

  const [, forceUpdate] = useState(0)

  useEffect(() => instance.subscribe(() => forceUpdate((value) => value + 1)), [instance])

  const translate = useCallback(
    (key: string, options?: TranslationOptions) => instance.t(key, options),
    [instance],
  )

  return useMemo(() => ({ t: translate, i18n: instance }), [instance, translate])
}
