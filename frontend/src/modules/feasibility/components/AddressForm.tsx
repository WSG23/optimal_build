import type { ChangeEvent, FormEvent } from 'react'

import type { WizardStatus } from '../types'

interface AddressFormProps {
  addressInput: string
  addressError: string | null
  status: WizardStatus
  onAddressChange: (event: ChangeEvent<HTMLInputElement>) => void
  onSubmit: (event: FormEvent<HTMLFormElement>) => void
  t: (key: string) => string
}

export function AddressForm({
  addressInput,
  addressError,
  status,
  onAddressChange,
  onSubmit,
  t,
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
