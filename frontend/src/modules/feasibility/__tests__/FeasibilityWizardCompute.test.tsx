import { vi, describe, it, expect, beforeEach } from 'vitest'
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react'
import React from 'react'
import { TranslationProvider } from '../../../i18n'
import { ThemeModeProvider } from '../../../theme/ThemeContext'
import { FeasibilityWizard } from '../FeasibilityWizard'
import {
  submitFeasibilityAssessment,
  type FeasibilityAssessmentResponse,
} from '../../../api/feasibility'

// Mock the API module
vi.mock('../../../api/feasibility', () => ({
  submitFeasibilityAssessment: vi.fn(),
  FeasibilityAssessmentRequest: {},
  getEngineeringDefaults: vi.fn().mockResolvedValue({
    typFloorToFloorM: 3.5,
    efficiencyRatio: 0.85,
  }),
}))

describe('FeasibilityWizard Compute Flow', () => {
  beforeEach(() => {
    cleanup()
    vi.clearAllMocks()
    const mockResponse: FeasibilityAssessmentResponse = {
      projectId: 'proj-123',
      summary: {
        maxPermissibleGfaSqm: 5000,
        estimatedAchievableGfaSqm: 4000,
        estimatedUnitCount: 40,
        siteCoveragePercent: 40,
        remarks: 'Test',
      },
      rules: [],
      recommendations: [],
      assetOptimizations: [],
      assetMixSummary: null,
      constraintLog: [],
      optimizerConfidence: 0.9,
    }
    vi.mocked(submitFeasibilityAssessment).mockResolvedValue(mockResponse)
  })

  it('collects address, site area, land use and submits correct payload', async () => {
    render(
      <ThemeModeProvider>
        <TranslationProvider>
          <FeasibilityWizard />
        </TranslationProvider>
      </ThemeModeProvider>,
    )

    // Fill Address
    const addressInput = screen.getByTestId('address-input')
    fireEvent.change(addressInput, { target: { value: '123 Main St' } })

    // Fill Site Area
    const siteAreaInput = screen.getByTestId('site-area-input')
    fireEvent.change(siteAreaInput, { target: { value: '1000' } })

    // Change Land Use (default is Mixed Use, change to Commercial)
    fireEvent.click(screen.getByRole('button', { name: 'Commercial' }))

    // Submit
    const submitBtn = screen.getByTestId('compute-button')
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(submitFeasibilityAssessment).toHaveBeenCalledTimes(1)
    })

    const callArgs = vi.mocked(submitFeasibilityAssessment).mock.calls[0][0]

    expect(callArgs.project.siteAddress).toBe('123 Main St')
    expect(callArgs.project.siteAreaSqm).toBe(1000)
    expect(callArgs.project.landUse).toBe('Commercial')
    // Name is generated
    expect(callArgs.project.name).toBe('Project 123 Main St')
  })
})
