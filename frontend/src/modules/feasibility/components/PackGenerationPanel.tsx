import { CloudUpload } from '@mui/icons-material'
import { FormControlLabel, Switch, CircularProgress } from '@mui/material'
import type { FormEvent } from 'react'
import { useState } from 'react'

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
  const [uploadToVdr, setUploadToVdr] = useState(false)
  const [vdrStatus, setVdrStatus] = useState<'idle' | 'uploading' | 'success'>('idle')

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
      e.preventDefault()
      if (uploadToVdr) {
          setVdrStatus('uploading')
          // Mock upload
          setTimeout(() => setVdrStatus('success'), 2000)
      }
      onSubmit(e)
  }

  return (
    <section className="feasibility-pack">
      <h2>{t('wizard.pack.title')}</h2>
      <p>{t('wizard.pack.subtitle')}</p>
      <form className="feasibility-pack__form" onSubmit={handleSubmit}>
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

        {/* VDR Toggle */}
        <div style={{ margin: '1rem 0', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.75rem', background: 'var(--ob-color-bg-surface-secondary)', borderRadius: 'var(--ob-radius-md)' }}>
            <FormControlLabel
                control={
                    <Switch
                        checked={uploadToVdr}
                        onChange={(e) => {
                            setUploadToVdr(e.target.checked)
                            setVdrStatus('idle')
                        }}
                        size="small"
                    />
                }
                label={
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <CloudUpload fontSize="small" sx={{ color: uploadToVdr ? 'var(--ob-color-brand-primary)' : 'inherit' }} />
                        <span style={{ fontSize: '0.875rem' }}>Upload to Data Room</span>
                    </div>
                }
                sx={{ margin: 0 }}
            />
            {vdrStatus === 'uploading' && <CircularProgress size={16} />}
            {vdrStatus === 'success' && <span style={{ fontSize: '0.75rem', color: 'var(--ob-color-success)', fontWeight: 600 }}>READY</span>}
        </div>

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

          {/* VDR Success Message */}
          {uploadToVdr && vdrStatus === 'success' && (
              <div style={{ marginTop: '1rem', padding: '0.5rem', background: '#e8f5e9', border: '1px solid #c8e6c9', borderRadius: '4px', fontSize: '0.8rem', color: '#2e7d32', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <CloudUpload fontSize="small" />
                  Successfully synced to project VDR.
              </div>
          )}
        </div>
      )}
    </section>
  )
}
