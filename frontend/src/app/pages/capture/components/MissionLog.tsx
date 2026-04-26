/**
 * MissionLog - Capture history table for unified capture page
 *
 * Displays a table of previously captured properties with:
 * - Target address
 * - District
 * - Scenario type
 * - Capture timestamp
 */

import { formatScenarioLabel } from '../utils/formatScenario'
import type { CapturedSite } from '../hooks/useUnifiedCapture'

export interface MissionLogProps {
  capturedSites: CapturedSite[]
}

export function MissionLog({ capturedSites }: MissionLogProps) {
  return (
    <section className="gps-page__captures">
      <div className="gps-panel">
        <h3>Mission Log</h3>
        {capturedSites.length === 0 ? (
          <p className="gps-panel__empty">No prior missions.</p>
        ) : (
          <table aria-label="Captured properties log">
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
                  <td>{site.district ?? '\u2014'}</td>
                  <td>
                    {site.scenario
                      ? formatScenarioLabel(site.scenario)
                      : '\u2014'}
                  </td>
                  <td>
                    {new Date(site.capturedAt).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  )
}
