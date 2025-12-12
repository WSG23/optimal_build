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
  hideAddress?: boolean
  hideSubmit?: boolean
}

export function AddressForm({
  addressInput,
  addressError,
  status,
  onAddressChange,
  onSubmit,
  t,
  siteAreaInput,
  onSiteAreaChange,
  hideAddress = false,
  hideSubmit = true, // Default to true as we have the FAB footer now
}: AddressFormProps) {
  // Shared Input Styles for Dark/Glass Theme
  const inputStyle = {
    background: 'rgba(255, 255, 255, 0.05)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    color: 'white',
    borderRadius: '6px',
    padding: '10px 12px',
    fontSize: '0.9rem',
    width: '100%',
    outline: 'none',
    transition: 'border-color 0.2s',
  }

  const labelStyle = {
    color: 'rgba(255, 255, 255, 0.7)',
    fontSize: '0.8rem',
    fontWeight: 500,
    marginBottom: '6px',
    display: 'block',
  }

  return (
    <form
      className="feasibility-form"
      onSubmit={onSubmit}
      noValidate
      style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}
    >
      {!hideAddress && (
        <div className="feasibility-form__field">
          <label style={labelStyle} htmlFor="address-input">
            {t('wizard.form.addressLabel')}
          </label>
          <input
            id="address-input"
            name="address"
            type="text"
            value={addressInput}
            onChange={onAddressChange}
            placeholder={t('wizard.form.addressPlaceholder')}
            data-testid="address-input"
            style={inputStyle}
          />
          {addressError && (
            <p className="feasibility-form__error" style={{ color: '#f87171' }}>
              {addressError}
            </p>
          )}
        </div>
      )}

      {siteAreaInput !== undefined && onSiteAreaChange && (
        <div className="feasibility-form__field">
          <label style={labelStyle} htmlFor="site-area-input">
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
            style={inputStyle}
          />
        </div>
      )}

      {!hideSubmit && (
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
      )}
    </form>
  )
}
