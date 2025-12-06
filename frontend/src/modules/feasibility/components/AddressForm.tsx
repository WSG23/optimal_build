import type { ChangeEvent, FormEvent } from 'react'

import type { WizardStatus } from '../types'

interface AddressFormProps {
  addressInput: string
  addressError: string | null
  status: WizardStatus
  onAddressChange: (event: ChangeEvent<HTMLInputElement>) => void
  onSubmit: (event: FormEvent<HTMLFormElement>) => void
  t: (key: string) => string
  siteAreaInput?: string
  landUseInput?: string
  onSiteAreaChange?: (event: ChangeEvent<HTMLInputElement>) => void
  onLandUseChange?: (event: ChangeEvent<HTMLSelectElement>) => void
}

export function AddressForm({
  addressInput,
  addressError,
  status,
  onAddressChange,
  onSubmit,
  t,
  siteAreaInput,
  landUseInput,
  onSiteAreaChange,
  onLandUseChange,
}: AddressFormProps) {
  return (
    <form className="feasibility-form" onSubmit={onSubmit} noValidate>
      <label className="feasibility-form__label" htmlFor="address-input">
        {t('wizard.form.addressLabel')}
      </label>
      <div className="feasibility-form__field">
        <input
          id="address-input"
          name="address"
          type="text"
          value={addressInput}
          onChange={onAddressChange}
          placeholder={t('wizard.form.addressPlaceholder')}
          data-testid="address-input"
        />
        {addressError && <p className="feasibility-form__error">{addressError}</p>}
      </div>

      {siteAreaInput !== undefined && onSiteAreaChange && (
        <div className="feasibility-form__field">
          <label className="feasibility-form__label" htmlFor="site-area-input">
            {t('wizard.form.siteAreaLabel') || 'Site Area (sqm)'}
          </label>
          <input
            id="site-area-input"
            name="siteArea"
            type="number"
            value={siteAreaInput}
            onChange={onSiteAreaChange}
            placeholder="e.g. 1000"
            data-testid="site-area-input"
          />
        </div>
      )}

      {landUseInput !== undefined && onLandUseChange && (
        <div className="feasibility-form__field">
          <label className="feasibility-form__label" htmlFor="land-use-input">
            {t('wizard.form.landUseLabel') || 'Land Use'}
          </label>
          <select
            id="land-use-input"
            name="landUse"
            value={landUseInput}
            onChange={onLandUseChange}
            data-testid="land-use-input"
          >
            <option value="Residential">Residential</option>
            <option value="Commercial">Commercial</option>
            <option value="Mixed Use">Mixed Use</option>
            <option value="Industrial">Industrial</option>
          </select>
        </div>
      )}

      <div className="feasibility-form__actions">
        <button
          type="submit"
          className="feasibility-form__submit"
          data-testid="compute-button"
        >
          {status === 'loading'
            ? t('wizard.form.submitLoading')
            : t('wizard.form.submitLabel')}
        </button>
      </div>
    </form>
  )
}
