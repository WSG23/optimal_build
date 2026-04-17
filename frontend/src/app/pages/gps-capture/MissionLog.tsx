/**
 * Mission Log
 *
 * Table of recently captured sites in the current session.
 * Extracted from GpsCapturePage for component size management.
 */

import type { DevelopmentScenario } from '../../../api/agents'
import { formatScenarioLabel } from './gpsCaptureUtils'

interface CapturedSite {
  propertyId: string
  address: string
  district?: string
  scenario: DevelopmentScenario | null
  capturedAt: string
}

interface MissionLogProps {
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
              color: 'var(--ob-color-text-muted, #94a3b8)',
            }}
          >
            No prior missions.
          </p>
        ) : (
          <table style={{ color: 'var(--ob-color-text-muted, #ccc)' }}>
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
