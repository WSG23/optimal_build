import { useState } from 'react'

import Step2Rules from './Step2Rules'
import type { FeasibilityRule, NewFeasibilityProjectInput } from './types'

const meta = {
  title: 'Feasibility/Step 2 · Rules',
  component: Step2Rules,
}

export default meta

const project: NewFeasibilityProjectInput = {
  name: 'Riverfront Residences',
  siteAddress: '123 Serangoon Ave 3',
  siteAreaSqm: 4125,
  landUse: 'residential',
  targetGrossFloorAreaSqm: 13800,
  buildingHeightMeters: 80,
}

const rules: FeasibilityRule[] = [
  {
    id: 'ura-plot-ratio',
    title: 'Plot ratio within URA master plan envelope',
    description: 'Maximum gross plot ratio permitted for the planning area.',
    authority: 'URA',
    topic: 'zoning',
    parameterKey: 'planning.gross_plot_ratio',
    operator: '<=',
    value: '3.5',
    severity: 'critical',
    defaultSelected: true,
  },
  {
    id: 'bca-site-coverage',
    title: 'Site coverage for residential developments',
    description: 'Site coverage must not exceed prescribed limits.',
    authority: 'BCA',
    topic: 'envelope',
    parameterKey: 'envelope.site_coverage_percent',
    operator: '<=',
    value: '45',
    unit: '%',
    severity: 'important',
    defaultSelected: true,
  },
  {
    id: 'scdf-access',
    title: 'Fire appliance access road width',
    description: 'Primary fire engine access roads must satisfy minimum width requirements.',
    authority: 'SCDF',
    topic: 'fire safety',
    parameterKey: 'fire.access.road_width_m',
    operator: '>=',
    value: '4.5',
    unit: 'm',
    severity: 'critical',
    defaultSelected: true,
  },
]

export const Default = () => {
  const [selected, setSelected] = useState(() => rules.map((rule) => rule.id))

  return (
    <div style={{ maxWidth: 960 }}>
      <Step2Rules
        project={project}
        rules={rules}
        summary={{
          complianceFocus: 'Envelope controls and critical access provisions',
          notes: 'Auto-selected based on residential land use profile',
        }}
        isLoading={false}
        error={null}
        selectedRuleIds={selected}
        onSelectionChange={setSelected}
        onBack={() => undefined}
        onContinue={() => undefined}
      />
    </div>
  )
}
