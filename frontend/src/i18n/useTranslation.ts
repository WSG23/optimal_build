import { useCallback, useContext, useEffect, useMemo, useState } from 'react'

import type { TranslationOptions } from './i18n'
import { I18nContext } from './context'

export function useTranslation() {
  const instance = useContext(I18nContext)

  const [, forceUpdate] = useState(0)

  useEffect(() => {
    const unsubscribe = instance.subscribe(() => {
      forceUpdate((value) => value + 1)
    })
    return unsubscribe
  }, [instance])

  const translate = useCallback(
    (key: string, options?: TranslationOptions) => instance.t(key, options),
    [instance],
  )

  return useMemo(
    () => ({ t: translate, i18n: instance }),
    [instance, translate],
  )
}
