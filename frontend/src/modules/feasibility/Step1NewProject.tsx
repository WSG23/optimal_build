import type { ChangeEvent, FormEvent } from 'react'
import { useEffect, useMemo, useState } from 'react'

import { useTranslation } from '../../i18n'

import { landUseOptions, LandUseType, NewFeasibilityProjectInput } from './types'

type Step1FieldKey =
  | 'name'
  | 'siteAddress'
  | 'siteAreaSqm'
  | 'landUse'
  | 'targetGrossFloorAreaSqm'
  | 'buildingHeightMeters'

export interface Step1FormValues {
  name: string
  siteAddress: string
  siteAreaSqm: string
  landUse: LandUseType | ''
  targetGrossFloorAreaSqm: string
  buildingHeightMeters: string
}

type Step1ErrorKey =
  | 'nameRequired'
  | 'siteAddressRequired'
  | 'siteAreaRequired'
  | 'siteAreaInvalid'
  | 'landUseRequired'
  | 'targetGfaInvalid'
  | 'heightInvalid'

type Step1FormErrors = Partial<Record<Step1FieldKey, Step1ErrorKey>>

const initialFormState: Step1FormValues = {
  name: '',
  siteAddress: '',
  siteAreaSqm: '',
  landUse: '',
  targetGrossFloorAreaSqm: '',
  buildingHeightMeters: '',
}

function formatDefaultValues(defaultValues?: NewFeasibilityProjectInput): Step1FormValues {
  if (!defaultValues) {
    return initialFormState
  }

  return {
    name: defaultValues.name ?? '',
    siteAddress: defaultValues.siteAddress ?? '',
    siteAreaSqm:
      defaultValues.siteAreaSqm !== undefined ? String(defaultValues.siteAreaSqm) : '',
    landUse: defaultValues.landUse ?? '',
    targetGrossFloorAreaSqm:
      defaultValues.targetGrossFloorAreaSqm !== undefined
        ? String(defaultValues.targetGrossFloorAreaSqm)
        : '',
    buildingHeightMeters:
      defaultValues.buildingHeightMeters !== undefined
        ? String(defaultValues.buildingHeightMeters)
        : '',
  }
}

interface Step1NewProjectProps {
  defaultValues?: NewFeasibilityProjectInput
  onSubmit: (values: NewFeasibilityProjectInput) => void
  isSubmitting?: boolean
}

export function Step1NewProject({
  defaultValues,
  onSubmit,
  isSubmitting = false,
}: Step1NewProjectProps) {
  const { t } = useTranslation()
  const [values, setValues] = useState<Step1FormValues>(() => formatDefaultValues(defaultValues))
  const [errors, setErrors] = useState<Step1FormErrors>({})

  useEffect(() => {
    setValues(formatDefaultValues(defaultValues))
    setErrors({})
  }, [defaultValues])

  const description = useMemo(() => t('wizard.step1.description'), [t])

  const handleFieldChange = (field: Step1FieldKey) =>
    (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
      const { value } = event.target
      setValues((previous) => ({ ...previous, [field]: value }))
      setErrors((previous) => ({ ...previous, [field]: undefined }))
    }

  const validateForm = (): Step1FormErrors | null => {
    const nextErrors: Step1FormErrors = {}

    if (!values.name.trim()) {
      nextErrors.name = 'nameRequired'
    }

    if (!values.siteAddress.trim()) {
      nextErrors.siteAddress = 'siteAddressRequired'
    }

    const siteArea = Number.parseFloat(values.siteAreaSqm)
    if (!values.siteAreaSqm.trim()) {
      nextErrors.siteAreaSqm = 'siteAreaRequired'
    } else if (!Number.isFinite(siteArea) || siteArea <= 0) {
      nextErrors.siteAreaSqm = 'siteAreaInvalid'
    }

    if (!values.landUse) {
      nextErrors.landUse = 'landUseRequired'
    }

    if (values.targetGrossFloorAreaSqm.trim()) {
      const targetGfa = Number.parseFloat(values.targetGrossFloorAreaSqm)
      if (!Number.isFinite(targetGfa) || targetGfa <= 0) {
        nextErrors.targetGrossFloorAreaSqm = 'targetGfaInvalid'
      }
    }

    if (values.buildingHeightMeters.trim()) {
      const height = Number.parseFloat(values.buildingHeightMeters)
      if (!Number.isFinite(height) || height <= 0) {
        nextErrors.buildingHeightMeters = 'heightInvalid'
      }
    }

    return Object.keys(nextErrors).length > 0 ? nextErrors : null
  }

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    const validationErrors = validateForm()
    if (validationErrors) {
      setErrors(validationErrors)
      return
    }

    const siteArea = Number.parseFloat(values.siteAreaSqm)
    const payload: NewFeasibilityProjectInput = {
      name: values.name.trim(),
      siteAddress: values.siteAddress.trim(),
      siteAreaSqm: siteArea,
      landUse: values.landUse as LandUseType,
    }

    if (values.targetGrossFloorAreaSqm.trim()) {
      payload.targetGrossFloorAreaSqm = Number.parseFloat(values.targetGrossFloorAreaSqm)
    }

    if (values.buildingHeightMeters.trim()) {
      payload.buildingHeightMeters = Number.parseFloat(values.buildingHeightMeters)
    }

    onSubmit(payload)
  }

  return (
    <div className="feasibility-step">
      <h2 className="feasibility-step__heading">{t('wizard.step1.heading')}</h2>
      <p className="feasibility-step__intro">{description}</p>

      <form className="feasibility-form" onSubmit={handleSubmit} noValidate>
        <div className="feasibility-form__field">
          <label htmlFor="name">{t('wizard.step1.fields.name.label')}</label>
          <input
            id="name"
            type="text"
            value={values.name}
            onChange={handleFieldChange('name')}
            placeholder={t('wizard.step1.fields.name.placeholder')}
          />
          {errors.name && (
            <p className="feasibility-form__error">{t(`wizard.step1.errors.${errors.name}`)}</p>
          )}
        </div>

        <div className="feasibility-form__field">
          <label htmlFor="siteAddress">{t('wizard.step1.fields.siteAddress.label')}</label>
          <input
            id="siteAddress"
            type="text"
            value={values.siteAddress}
            onChange={handleFieldChange('siteAddress')}
            placeholder={t('wizard.step1.fields.siteAddress.placeholder')}
          />
          {errors.siteAddress && (
            <p className="feasibility-form__error">{t(`wizard.step1.errors.${errors.siteAddress}`)}</p>
          )}
        </div>

        <div className="feasibility-form__field">
          <label htmlFor="siteAreaSqm">{t('wizard.step1.fields.siteAreaSqm.label')}</label>
          <input
            id="siteAreaSqm"
            type="number"
            step="0.01"
            value={values.siteAreaSqm}
            onChange={handleFieldChange('siteAreaSqm')}
            placeholder={t('wizard.step1.fields.siteAreaSqm.placeholder')}
          />
          {errors.siteAreaSqm && (
            <p className="feasibility-form__error">{t(`wizard.step1.errors.${errors.siteAreaSqm}`)}</p>
          )}
        </div>

        <div className="feasibility-form__field">
          <label htmlFor="landUse">{t('wizard.step1.fields.landUse.label')}</label>
          <select id="landUse" value={values.landUse} onChange={handleFieldChange('landUse')}>
            <option value="">{t('wizard.step1.fields.landUse.placeholder')}</option>
            {landUseOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {t(option.labelKey)}
              </option>
            ))}
          </select>
          {errors.landUse && (
            <p className="feasibility-form__error">{t(`wizard.step1.errors.${errors.landUse}`)}</p>
          )}
        </div>

        <div className="feasibility-form__grid">
          <div className="feasibility-form__field">
            <label htmlFor="targetGrossFloorAreaSqm">
              {t('wizard.step1.fields.targetGrossFloorAreaSqm.label')}
            </label>
            <input
              id="targetGrossFloorAreaSqm"
              type="number"
              step="0.01"
              value={values.targetGrossFloorAreaSqm}
              onChange={handleFieldChange('targetGrossFloorAreaSqm')}
              placeholder={t('wizard.step1.fields.targetGrossFloorAreaSqm.placeholder')}
            />
            {errors.targetGrossFloorAreaSqm && (
              <p className="feasibility-form__error">
                {t(`wizard.step1.errors.${errors.targetGrossFloorAreaSqm}`)}
              </p>
            )}
          </div>

          <div className="feasibility-form__field">
            <label htmlFor="buildingHeightMeters">
              {t('wizard.step1.fields.buildingHeightMeters.label')}
            </label>
            <input
              id="buildingHeightMeters"
              type="number"
              step="0.1"
              value={values.buildingHeightMeters}
              onChange={handleFieldChange('buildingHeightMeters')}
              placeholder={t('wizard.step1.fields.buildingHeightMeters.placeholder')}
            />
            {errors.buildingHeightMeters && (
              <p className="feasibility-form__error">
                {t(`wizard.step1.errors.${errors.buildingHeightMeters}`)}
              </p>
            )}
          </div>
        </div>

        <button className="feasibility-form__submit" type="submit" disabled={isSubmitting}>
          {isSubmitting ? t('wizard.step1.actions.saving') : t('wizard.step1.actions.continue')}
        </button>
      </form>
    </div>
  )
}

export default Step1NewProject
