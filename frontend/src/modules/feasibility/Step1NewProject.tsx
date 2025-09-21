import type { ChangeEvent, FormEvent } from 'react'
import { useEffect, useMemo, useState } from 'react'

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

type Step1FormErrors = Partial<Record<Step1FieldKey, string>>

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
  const [values, setValues] = useState<Step1FormValues>(() => formatDefaultValues(defaultValues))
  const [errors, setErrors] = useState<Step1FormErrors>({})

  useEffect(() => {
    setValues(formatDefaultValues(defaultValues))
    setErrors({})
  }, [defaultValues])

  const description = useMemo(
    () =>
      `Capture the essential site information that powers compliance lookups. ` +
      `This data will be used to determine zoning, plot ratio and envelope controls before fetching applicable rules.`,
    [],
  )

  const handleFieldChange = (field: Step1FieldKey) =>
    (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
      const { value } = event.target
      setValues((previous) => ({ ...previous, [field]: value }))
      setErrors((previous) => ({ ...previous, [field]: undefined }))
    }

  const validateForm = (): Step1FormErrors | null => {
    const nextErrors: Step1FormErrors = {}

    if (!values.name.trim()) {
      nextErrors.name = 'Project name is required'
    }

    if (!values.siteAddress.trim()) {
      nextErrors.siteAddress = 'Site address is required'
    }

    const siteArea = Number.parseFloat(values.siteAreaSqm)
    if (!values.siteAreaSqm.trim()) {
      nextErrors.siteAreaSqm = 'Site area is required'
    } else if (!Number.isFinite(siteArea) || siteArea <= 0) {
      nextErrors.siteAreaSqm = 'Site area must be greater than zero'
    }

    if (!values.landUse) {
      nextErrors.landUse = 'Select a land use to continue'
    }

    if (values.targetGrossFloorAreaSqm.trim()) {
      const targetGfa = Number.parseFloat(values.targetGrossFloorAreaSqm)
      if (!Number.isFinite(targetGfa) || targetGfa <= 0) {
        nextErrors.targetGrossFloorAreaSqm = 'Target GFA must be greater than zero'
      }
    }

    if (values.buildingHeightMeters.trim()) {
      const height = Number.parseFloat(values.buildingHeightMeters)
      if (!Number.isFinite(height) || height <= 0) {
        nextErrors.buildingHeightMeters = 'Height must be greater than zero'
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
      <h2 className="feasibility-step__heading">Step 1 · New project details</h2>
      <p className="feasibility-step__intro">{description}</p>

      <form className="feasibility-form" onSubmit={handleSubmit} noValidate>
        <div className="feasibility-form__field">
          <label htmlFor="name">Project name</label>
          <input
            id="name"
            type="text"
            value={values.name}
            onChange={handleFieldChange('name')}
            placeholder="e.g. Riverfront Residences"
          />
          {errors.name && <p className="feasibility-form__error">{errors.name}</p>}
        </div>

        <div className="feasibility-form__field">
          <label htmlFor="siteAddress">Site address</label>
          <input
            id="siteAddress"
            type="text"
            value={values.siteAddress}
            onChange={handleFieldChange('siteAddress')}
            placeholder="e.g. 123 Serangoon Ave 3"
          />
          {errors.siteAddress && <p className="feasibility-form__error">{errors.siteAddress}</p>}
        </div>

        <div className="feasibility-form__field">
          <label htmlFor="siteAreaSqm">Site area (sqm)</label>
          <input
            id="siteAreaSqm"
            type="number"
            step="0.01"
            value={values.siteAreaSqm}
            onChange={handleFieldChange('siteAreaSqm')}
            placeholder="e.g. 4250"
          />
          {errors.siteAreaSqm && <p className="feasibility-form__error">{errors.siteAreaSqm}</p>}
        </div>

        <div className="feasibility-form__field">
          <label htmlFor="landUse">Land use</label>
          <select id="landUse" value={values.landUse} onChange={handleFieldChange('landUse')}>
            <option value="">Select a land use</option>
            {landUseOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          {errors.landUse && <p className="feasibility-form__error">{errors.landUse}</p>}
        </div>

        <div className="feasibility-form__grid">
          <div className="feasibility-form__field">
            <label htmlFor="targetGrossFloorAreaSqm">Target GFA (sqm)</label>
            <input
              id="targetGrossFloorAreaSqm"
              type="number"
              step="0.01"
              value={values.targetGrossFloorAreaSqm}
              onChange={handleFieldChange('targetGrossFloorAreaSqm')}
              placeholder="Optional"
            />
            {errors.targetGrossFloorAreaSqm && (
              <p className="feasibility-form__error">{errors.targetGrossFloorAreaSqm}</p>
            )}
          </div>

          <div className="feasibility-form__field">
            <label htmlFor="buildingHeightMeters">Target height (m)</label>
            <input
              id="buildingHeightMeters"
              type="number"
              step="0.1"
              value={values.buildingHeightMeters}
              onChange={handleFieldChange('buildingHeightMeters')}
              placeholder="Optional"
            />
            {errors.buildingHeightMeters && (
              <p className="feasibility-form__error">{errors.buildingHeightMeters}</p>
            )}
          </div>
        </div>

        <button className="feasibility-form__submit" type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Saving…' : 'Continue to rules'}
        </button>
      </form>
    </div>
  )
}

export default Step1NewProject
