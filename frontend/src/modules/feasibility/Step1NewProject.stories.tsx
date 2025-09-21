import Step1NewProject from './Step1NewProject'
import type { NewFeasibilityProjectInput } from './types'

const meta = {
  title: 'Feasibility/Step 1 · New project',
  component: Step1NewProject,
}

export default meta

const sampleProject: NewFeasibilityProjectInput = {
  name: 'Riverfront Residences',
  siteAddress: '123 Serangoon Ave 3',
  siteAreaSqm: 4125,
  landUse: 'residential',
  targetGrossFloorAreaSqm: 13800,
  buildingHeightMeters: 80,
}

export const Default = () => (
  <div style={{ maxWidth: 720 }}>
    <Step1NewProject defaultValues={sampleProject} onSubmit={console.log} />
  </div>
)
