import { render, screen } from '@testing-library/react'
import type { ReactNode } from 'react'
import { describe, expect, it, vi } from 'vitest'

import type { SiteAcquisitionResult } from '../../../../../api/siteAcquisition'
import { MultiScenarioComparisonSection } from './MultiScenarioComparisonSection'

vi.mock('../../../../../router', () => ({
  Link: ({
    children,
    to,
    className,
  }: {
    children: ReactNode
    to: string
    className?: string
  }) => (
    <a href={to} className={className}>
      {children}
    </a>
  ),
}))

describe('MultiScenarioComparisonSection', () => {
  it('renders capture-native metrics and omits due diligence labels', () => {
    render(
      <MultiScenarioComparisonSection
        capturedProperty={
          {
            propertyId: 'prop-1',
            quickAnalysis: {
              generatedAt: '2026-01-06T10:00:00Z',
              scenarios: [],
            },
            buildEnvelope: {
              zoneCode: 'C',
              zoneDescription: 'Commercial',
              siteAreaSqm: 5000,
              allowablePlotRatio: 4.2,
              maxBuildableGfaSqm: 21000,
              currentGfaSqm: 18000,
              additionalPotentialGfaSqm: 3000,
              buildingHeightLimitM: 120,
              siteCoveragePct: 80,
              assumptions: [],
              sourceReference: null,
            },
            visualization: {
              status: 'queued',
              previewAvailable: false,
              notes: [],
              conceptMeshUrl: null,
              previewMetadataUrl: null,
              thumbnailUrl: null,
              cameraOrbitHint: null,
              previewSeed: null,
              previewJobId: null,
              massingLayers: [],
              colorLegend: [],
            },
            heritageContext: null,
          } as SiteAcquisitionResult
        }
        quickAnalysisScenariosCount={2}
        scenarioComparisonData={[
          {
            key: 'raw_land',
            label: 'New Construction',
            icon: '🏗️',
            quickHeadline: 'Envelope supports high-density buildout',
            quickMetrics: [
              {
                key: 'potential_gfa_sqm',
                label: 'Potential GFA (sqm)',
                value: '20,000 sqm',
              },
            ],
          },
        ]}
        feasibilitySignals={[
          {
            scenario: 'raw_land',
            label: 'New Construction',
            opportunities: ['Potential GFA of 20,000 sqm'],
            risks: ['Plot ratio unavailable'],
          },
        ]}
        comparisonScenariosCount={1}
        activeScenario="raw_land"
        scenarioLookup={new Map([['raw_land', { label: 'New Construction' }]])}
        propertyId="prop-1"
        setActiveScenario={() => undefined}
        formatRecordedTimestamp={() => 'Jan 6, 2026, 10:00 AM'}
      />,
    )

    expect(screen.getByText('CAPTURE COVERAGE')).toBeInTheDocument()
    expect(screen.getByText('CONSTRAINT FLAGS')).toBeInTheDocument()
    expect(screen.getByText('BUILDABLE GFA')).toBeInTheDocument()
    expect(screen.getByText('NEW CONSTRUCTION')).toBeInTheDocument()
    expect(screen.getByText(/SCENARIO FOCUS:/i)).toBeInTheDocument()
    expect(screen.getByText(/Viewing New Construction\./i)).toBeInTheDocument()
    expect(screen.getByText('AVG_COVERAGE')).toBeInTheDocument()
    expect(screen.getByText('CONSTRAINTS_FLAGGED')).toBeInTheDocument()
    expect(screen.getByText('INSTANT_SIGNALS (1)')).toBeInTheDocument()
    expect(
      screen.getByRole('link', { name: /continue to feasibility/i }),
    ).toHaveAttribute('href', '/app/asset-feasibility?propertyId=prop-1')
    expect(screen.queryByText('DILIGENCE GAUGE')).not.toBeInTheDocument()
    expect(screen.queryByText('AVG_CONDITION')).not.toBeInTheDocument()
    expect(screen.queryByText('RISK VECTOR')).not.toBeInTheDocument()
    expect(screen.queryByText('JSON')).not.toBeInTheDocument()
    expect(screen.queryByText('PDF')).not.toBeInTheDocument()
  })
})
