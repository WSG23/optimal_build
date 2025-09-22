import { createContext } from 'react'

import i18n, { I18n } from './i18n'

export const I18nContext = createContext<I18n>(i18n)
