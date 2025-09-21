import CadDetectionPreview from './CadDetectionPreview'
import { TranslationProvider } from '../../i18n'
import type { DetectedUnit } from './types'

const meta = {
  title: 'CAD/Detection Preview',
  component: CadDetectionPreview,
}

export default meta

const units: DetectedUnit[] = [
  { id: 'L01-01', floor: 1, unitLabel: '#01-01', areaSqm: 82, status: 'source' },
  { id: 'L01-02', floor: 1, unitLabel: '#01-02', areaSqm: 79, status: 'pending' },
  { id: 'L02-01', floor: 2, unitLabel: '#02-01', areaSqm: 85, status: 'approved' },
  { id: 'L03-01', floor: 3, unitLabel: '#03-01', areaSqm: 90, status: 'rejected' },
]

export const Default = () => (
  <TranslationProvider>
    <CadDetectionPreview
      units={units}
      overlays={['fire_access', 'community_facility']}
      hints={['Coordinate with SCDF on staging']}
      zoneCode="RA"
    />
  </TranslationProvider>
)

export const Locked = () => (
  <TranslationProvider>
    <CadDetectionPreview
      units={units.filter((unit) => unit.status !== 'rejected')}
      overlays={[]}
      hints={['Awaiting overlays']}
      zoneCode="CBD"
      locked
    />
  </TranslationProvider>
)
