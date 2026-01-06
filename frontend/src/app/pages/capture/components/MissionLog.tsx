/**
 * MissionLog - Capture history table for unified capture page
 *
 * Displays a table of previously captured properties with:
 * - Target address
 * - District
 * - Scenario type
 * - Capture timestamp
 */

import type { DevelopmentScenario } from '../../../../api/agents'

export interface CapturedSite {
  propertyId: string
  address: string
  district?: string
  scenario: DevelopmentScenario | null
  capturedAt: string
}

export interface MissionLogProps {
  capturedSites: CapturedSite[]
}

export function MissionLog({ capturedSites }: MissionLogProps) {
  return (
    <section className="gps-page__captures">
      <div className="gps-panel">
        <h3>Mission Log</h3>
        {capturedSites.length === 0 ? (
          <p
            style={{
              fontStyle: 'italic',
              color: 'var(--ob-color-text-tertiary)',
            }}
          >
            No prior missions.
          </p>
        ) : (
          <table style={{ color: 'var(--ob-color-text-secondary)' }}>
            <thead>
              <tr>
                <th>Target</th>
                <th>District</th>
                <th>Scenario</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {capturedSites.map((site) => (
                <tr key={`${site.propertyId}-${site.capturedAt}`}>
                  <td>{site.address}</td>
                  <td>{site.district ?? '-'}</td>
                  <td>
                    {site.scenario ? formatScenarioLabel(site.scenario) : '-'}
                  </td>
                  <td>{new Date(site.capturedAt).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  )
}

function formatScenarioLabel(value: DevelopmentScenario) {
  switch (value) {
    case 'raw_land':
      return 'Raw land'
    case 'existing_building':
      return 'Existing building'
    case 'heritage_property':
      return 'Heritage property'
    case 'underused_asset':
      return 'Underused asset'
    case 'mixed_use_redevelopment':
      return 'Mixed-use redevelopment'
    default:
      return value
  }
}
