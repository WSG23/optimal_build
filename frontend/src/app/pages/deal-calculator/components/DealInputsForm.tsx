import React, { useState } from 'react'
import {
  Box,
  Collapse,
  Grid,
  IconButton,
  MenuItem,
  Select,
  Stack,
  Tooltip,
  Typography,
} from '@mui/material'
import { ExpandMore, ExpandLess } from '@mui/icons-material'

import { Button } from '../../../../components/canonical/Button'
import { Card } from '../../../../components/canonical/Card'
import { Input } from '../../../../components/canonical/Input'
import { AlertBlock } from '../../../../components/canonical/AlertBlock'
import type { FormState } from './dealFormState'

interface DealInputsFormProps {
  form: FormState
  onFormChange: (form: FormState) => void
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => void
  isSubmitting: boolean
  error: string | null
}

function isPositiveNumber(value: string): boolean {
  const n = Number(value)
  return value.trim() !== '' && !isNaN(n) && n > 0
}

function isPercentage(value: string): boolean {
  const n = Number(value)
  return value.trim() !== '' && !isNaN(n) && n >= 0 && n <= 100
}

function isPositiveInteger(value: string): boolean {
  const n = Number(value)
  return value.trim() !== '' && Number.isInteger(n) && n > 0
}

export function DealInputsForm({
  form,
  onFormChange,
  onSubmit,
  isSubmitting,
  error,
}: DealInputsFormProps) {
  const [financeOpen, setFinanceOpen] = useState(false)
  const [validationErrors, setValidationErrors] = useState<
    Record<string, string>
  >({})
  const isManualMode = form.address.trim().length === 0

  const validate = (state: FormState): Record<string, string> => {
    const errors: Record<string, string> = {}
    if (!state.projectName.trim()) {
      errors.projectName = 'Project name is required'
    }
    if (
      state.address.trim() === '' &&
      !state.landUse.trim() &&
      !state.zoneCode.trim() &&
      !state.siteAreaSqm.trim()
    ) {
      errors.address = 'Address or manual site assumptions are required'
    }
    if (!isPositiveNumber(state.siteAreaSqm)) {
      errors.siteAreaSqm = 'Must be a positive number'
    }
    if (!isPositiveNumber(state.allowablePlotRatio)) {
      errors.allowablePlotRatio = 'Must be a positive number'
    }
    if (!isPositiveNumber(state.targetGrossFloorAreaSqm)) {
      errors.targetGrossFloorAreaSqm = 'Must be a positive number'
    }
    if (!isPercentage(state.equityPct)) {
      errors.equityPct = 'Must be 0-100'
    }
    if (!isPercentage(state.debtPct)) {
      errors.debtPct = 'Must be 0-100'
    }
    if (!isPercentage(state.annualInterestRatePct)) {
      errors.annualInterestRatePct = 'Must be 0-100'
    }
    if (!isPercentage(state.discountRatePct)) {
      errors.discountRatePct = 'Must be 0-100'
    }
    if (!isPercentage(state.exitCapRatePct)) {
      errors.exitCapRatePct = 'Must be 0-100'
    }
    if (!isPositiveInteger(state.holdYears)) {
      errors.holdYears = 'Must be a positive integer'
    }
    return errors
  }

  const hasValidationErrors = Object.keys(validationErrors).length > 0

  const updateField =
    (key: keyof FormState) =>
    (
      event: React.ChangeEvent<
        HTMLInputElement | HTMLTextAreaElement | { value: unknown }
      >,
    ) => {
      const value = (event.target as HTMLInputElement).value
      onFormChange({ ...form, [key]: value })
      setValidationErrors((prev) => {
        const next = { ...prev }
        delete next[key]
        return next
      })
    }

  const updateSelect =
    (key: keyof FormState) => (event: { target: { value: string } }) => {
      onFormChange({ ...form, [key]: event.target.value })
    }

  return (
    <Card
      variant="default"
      sx={{
        p: 'var(--ob-space-200)',
        position: { md: 'sticky' },
        top: { md: 'var(--ob-space-200)' },
      }}
    >
      <Typography
        variant="overline"
        sx={{
          color: 'var(--ob-color-text-secondary)',
          letterSpacing: '0.08em',
        }}
      >
        Top-of-funnel
      </Typography>
      <Typography
        variant="h5"
        sx={{
          fontWeight: 700,
          mt: 'var(--ob-space-050)',
          mb: 'var(--ob-space-050)',
        }}
      >
        Deal calculator
      </Typography>
      <Typography
        variant="body2"
        sx={{
          color: 'var(--ob-color-text-secondary)',
          mb: 'var(--ob-space-200)',
        }}
      >
        Paste a Singapore address or switch to manual assumptions. Returns build
        envelope, feasibility, and quick finance in one pass.
      </Typography>

      <form
        onSubmit={(e) => {
          e.preventDefault()
          const errors = validate(form)
          setValidationErrors(errors)
          if (Object.keys(errors).length > 0) return
          onSubmit(e)
        }}
        aria-label="Deal screening form"
      >
        <Stack spacing="var(--ob-space-150)">
          <Input
            label="Project name"
            value={form.projectName}
            onChange={updateField('projectName')}
            size="small"
            error={Boolean(validationErrors.projectName)}
            helperText={validationErrors.projectName}
          />
          <Input
            label="Address"
            value={form.address}
            onChange={updateField('address')}
            placeholder="1 Marina Boulevard, Singapore"
            size="small"
            error={Boolean(validationErrors.address)}
            helperText={
              validationErrors.address ??
              (isManualMode
                ? 'Leave blank to run from manual site assumptions.'
                : undefined)
            }
          />

          {isManualMode && (
            <AlertBlock type="info" variant="outlined">
              Manual mode active. Fill in site parameters below.
            </AlertBlock>
          )}

          <Grid container spacing="var(--ob-space-100)">
            <Grid item xs={12} sm={6}>
              <Box>
                <Typography
                  component="label"
                  variant="caption"
                  sx={{
                    display: 'block',
                    mb: 'var(--ob-space-025)',
                    color: 'var(--ob-color-text-secondary)',
                    fontWeight: 'var(--ob-font-weight-medium)',
                  }}
                >
                  Land use
                </Typography>
                <Select
                  value={form.landUse}
                  onChange={updateSelect('landUse')}
                  size="small"
                  fullWidth
                  sx={{
                    borderRadius: 'var(--ob-radius-sm)',
                    fontSize: 'var(--ob-font-size-sm)',
                  }}
                >
                  <MenuItem value="residential">Residential</MenuItem>
                  <MenuItem value="commercial">Commercial</MenuItem>
                  <MenuItem value="mixed_use">Mixed use</MenuItem>
                  <MenuItem value="industrial">Industrial</MenuItem>
                </Select>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Input
                label="Zone code"
                value={form.zoneCode}
                onChange={updateField('zoneCode')}
                size="small"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Input
                label="Site area (sqm)"
                value={form.siteAreaSqm}
                onChange={updateField('siteAreaSqm')}
                size="small"
                inputProps={{ inputMode: 'decimal' }}
                error={Boolean(validationErrors.siteAreaSqm)}
                helperText={validationErrors.siteAreaSqm}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Tooltip
                title="Maximum ratio of floor area to land area allowed by zoning"
                arrow
                placement="top"
              >
                <div>
                  <Input
                    label="Plot ratio"
                    value={form.allowablePlotRatio}
                    onChange={updateField('allowablePlotRatio')}
                    size="small"
                    inputProps={{ inputMode: 'decimal' }}
                    error={Boolean(validationErrors.allowablePlotRatio)}
                    helperText={validationErrors.allowablePlotRatio}
                  />
                </div>
              </Tooltip>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Tooltip
                title="Current Gross Floor Area of existing structures on site"
                arrow
                placement="top"
              >
                <div>
                  <Input
                    label="Current GFA"
                    value={form.currentGfaSqm}
                    onChange={updateField('currentGfaSqm')}
                    size="small"
                    inputProps={{ inputMode: 'decimal' }}
                  />
                </div>
              </Tooltip>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Tooltip
                title="Target Gross Floor Area for the proposed development"
                arrow
                placement="top"
              >
                <div>
                  <Input
                    label="Target GFA"
                    value={form.targetGrossFloorAreaSqm}
                    onChange={updateField('targetGrossFloorAreaSqm')}
                    size="small"
                    inputProps={{ inputMode: 'decimal' }}
                    error={Boolean(validationErrors.targetGrossFloorAreaSqm)}
                    helperText={validationErrors.targetGrossFloorAreaSqm}
                  />
                </div>
              </Tooltip>
            </Grid>
          </Grid>

          <Box
            sx={{
              borderTop: 'var(--ob-border-fine)',
              pt: 'var(--ob-space-100)',
            }}
          >
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                cursor: 'pointer',
              }}
              onClick={() => setFinanceOpen((prev) => !prev)}
              role="button"
              aria-expanded={financeOpen}
              aria-controls="finance-assumptions"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  setFinanceOpen((prev) => !prev)
                }
              }}
            >
              <Typography
                variant="subtitle2"
                sx={{ fontWeight: 'var(--ob-font-weight-semibold)' }}
              >
                Finance assumptions
              </Typography>
              <IconButton size="small" tabIndex={-1} aria-hidden>
                {financeOpen ? <ExpandLess /> : <ExpandMore />}
              </IconButton>
            </Box>
            <Collapse in={financeOpen} id="finance-assumptions">
              <Grid
                container
                spacing="var(--ob-space-100)"
                sx={{ mt: 'var(--ob-space-050)' }}
              >
                <Grid item xs={12} sm={6}>
                  <Input
                    label="Equity %"
                    value={form.equityPct}
                    onChange={updateField('equityPct')}
                    size="small"
                    inputProps={{ inputMode: 'decimal' }}
                    error={Boolean(validationErrors.equityPct)}
                    helperText={validationErrors.equityPct}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Input
                    label="Debt %"
                    value={form.debtPct}
                    onChange={updateField('debtPct')}
                    size="small"
                    inputProps={{ inputMode: 'decimal' }}
                    error={Boolean(validationErrors.debtPct)}
                    helperText={validationErrors.debtPct}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Input
                    label="Interest %"
                    value={form.annualInterestRatePct}
                    onChange={updateField('annualInterestRatePct')}
                    size="small"
                    inputProps={{ inputMode: 'decimal' }}
                    error={Boolean(validationErrors.annualInterestRatePct)}
                    helperText={validationErrors.annualInterestRatePct}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Tooltip
                    title="Rate used to discount future cash flows to present value"
                    arrow
                    placement="top"
                  >
                    <div>
                      <Input
                        label="Discount %"
                        value={form.discountRatePct}
                        onChange={updateField('discountRatePct')}
                        size="small"
                        inputProps={{ inputMode: 'decimal' }}
                        error={Boolean(validationErrors.discountRatePct)}
                        helperText={validationErrors.discountRatePct}
                      />
                    </div>
                  </Tooltip>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Tooltip
                    title="Capitalization rate applied to NOI to estimate exit value"
                    arrow
                    placement="top"
                  >
                    <div>
                      <Input
                        label="Exit cap %"
                        value={form.exitCapRatePct}
                        onChange={updateField('exitCapRatePct')}
                        size="small"
                        inputProps={{ inputMode: 'decimal' }}
                        error={Boolean(validationErrors.exitCapRatePct)}
                        helperText={validationErrors.exitCapRatePct}
                      />
                    </div>
                  </Tooltip>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Input
                    label="Hold years"
                    value={form.holdYears}
                    onChange={updateField('holdYears')}
                    size="small"
                    inputProps={{ inputMode: 'numeric' }}
                    error={Boolean(validationErrors.holdYears)}
                    helperText={validationErrors.holdYears}
                  />
                </Grid>
              </Grid>
            </Collapse>
          </Box>

          <Button
            type="submit"
            variant="primary"
            size="lg"
            disabled={isSubmitting || hasValidationErrors}
            sx={{ width: '100%' }}
          >
            {isSubmitting ? 'Running screen...' : 'Run deal screen'}
          </Button>

          {error && <AlertBlock type="error">{error}</AlertBlock>}
        </Stack>
      </form>
    </Card>
  )
}
