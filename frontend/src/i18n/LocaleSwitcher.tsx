import type { ChangeEvent } from 'react'
import { useCallback } from 'react'

import { supportedLanguages, useTranslation } from './index'

export function LocaleSwitcher() {
  const { i18n, t } = useTranslation()
  const currentLanguage = i18n.resolvedLanguage ?? i18n.language

  const handleChange = useCallback(
    (event: ChangeEvent<HTMLSelectElement>) => {
      const nextLanguage = event.target.value
      void i18n.changeLanguage(nextLanguage)
    },
    [i18n],
  )

  return (
    <div className="locale-switcher">
      <label className="locale-switcher__label" htmlFor="app-locale-select">
        {t('common.language.label')}
      </label>
      <select
        id="app-locale-select"
        className="locale-switcher__select"
        value={currentLanguage}
        onChange={handleChange}
      >
        {supportedLanguages.map((language) => (
          <option key={language.value} value={language.value}>
            {t(language.labelKey)}
          </option>
        ))}
      </select>
    </div>
  )
}

export default LocaleSwitcher
