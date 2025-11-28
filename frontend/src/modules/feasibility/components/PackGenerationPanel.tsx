import type { FormEvent } from 'react'

import type { ProfessionalPackSummary, ProfessionalPackType } from '../../../api/agents'
import type { PackOption } from '../types'
import { PACK_OPTIONS } from '../types'
import { formatFileSize } from '../utils/formatters'

interface PackGenerationPanelProps {
  packPropertyId: string
  packType: ProfessionalPackType
  packSummary: ProfessionalPackSummary | null
  packLoading: boolean
  packError: string | null
  selectedPackOption: PackOption
  locale: string
  onPropertyIdChange: (value: string) => void
  onPackTypeChange: (value: ProfessionalPackType) => void
  onSubmit: (event: FormEvent<HTMLFormElement>) => void
  t: (key: string, options?: Record<string, unknown>) => string
}

export function PackGenerationPanel({
  packPropertyId,
  packType,
  packSummary,
  packLoading,
  packError,
  selectedPackOption,
  locale,
  onPropertyIdChange,
  onPackTypeChange,
  onSubmit,
  t,
}: PackGenerationPanelProps) {
  return (
    <section className="feasibility-pack">
      <h2>{t('wizard.pack.title')}</h2>
      <p>{t('wizard.pack.subtitle')}</p>
      <form className="feasibility-pack__form" onSubmit={onSubmit}>
        <label className="feasibility-pack__field">
          <span>{t('wizard.pack.propertyLabel')}</span>
          <input
            type="text"
            value={packPropertyId}
            onChange={(event) => onPropertyIdChange(event.target.value)}
            placeholder={t('wizard.pack.propertyPlaceholder')}
            data-testid="feasibility-pack-property"
          />
          <small>{t('wizard.pack.propertyHelper')}</small>
        </label>
        <label className="feasibility-pack__field">
          <span>{t('wizard.pack.typeLabel')}</span>
          <select
            value={packType}
            onChange={(event) =>
              onPackTypeChange(event.target.value as ProfessionalPackType)
            }
            data-testid="feasibility-pack-type"
          >
            {PACK_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {t(option.labelKey)}
              </option>
            ))}
          </select>
          <small>{t(selectedPackOption.descriptionKey)}</small>
        </label>
        <button
          type="submit"
          className="feasibility-pack__submit"
          disabled={packLoading}
          data-testid="feasibility-pack-submit"
        >
          {packLoading ? t('wizard.pack.generateLoading') : t('wizard.pack.generate')}
        </button>
      </form>
      {packError && (
        <p className="feasibility-pack__error" role="alert">
          {t('wizard.pack.error', { message: packError })}
        </p>
      )}
      {packSummary && (
        <div className="feasibility-pack__result">
          <p>
            {t('wizard.pack.generatedAt', {
              timestamp: new Date(packSummary.generatedAt).toLocaleString(locale),
            })}
          </p>
          <p>
            {t('wizard.pack.size', {
              size: formatFileSize(packSummary.sizeBytes, locale),
            })}
          </p>
          {packSummary.downloadUrl ? (
            <a
              href={packSummary.downloadUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="feasibility-pack__download"
            >
              {t('wizard.pack.downloadCta', {
                filename: packSummary.filename,
              })}
            </a>
          ) : (
            <p>{t('wizard.pack.noDownload')}</p>
          )}
        </div>
      )}
    </section>
  )
}
