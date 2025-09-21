import Step3Buildable from './Step3Buildable'
import type { FeasibilityAssessmentResponse } from './types'

const meta = {
  title: 'Feasibility/Step 3 · Buildability',
  component: Step3Buildable,
}

export default meta

const assessment: FeasibilityAssessmentResponse = {
  projectId: 'project-Riverfront Residences',
  summary: {
    maxPermissibleGfaSqm: 14438,
    estimatedAchievableGfaSqm: 11839,
    estimatedUnitCount: 140,
    siteCoveragePercent: 38.5,
    remarks: 'Envelope complies with current zoning allowances.',
  },
  rules: [
    {
      id: 'ura-plot-ratio',
      title: 'Plot ratio within URA master plan envelope',
      description: 'Maximum gross plot ratio permitted for the planning area according to the 2025 URA plan.',
      authority: 'URA',
      topic: 'zoning',
      parameterKey: 'planning.gross_plot_ratio',
      operator: '<=',
      value: '3.5',
      severity: 'critical',
      defaultSelected: true,
      status: 'pass',
      notes: 'Design meets required plot ratio.',
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
      status: 'warning',
      notes: 'Review secondary access – marginal clearance observed.',
    },
  ],
  recommendations: [
    'Coordinate with the fire consultant to confirm appliance access turning radii.',
    'Prepare submission pack with the generated feasibility summary for management review.',
  ],
}

export const Default = () => (
  <div style={{ maxWidth: 960 }}>
    <Step3Buildable assessment={assessment} onBack={() => undefined} onRestart={() => undefined} />
  </div>
)
