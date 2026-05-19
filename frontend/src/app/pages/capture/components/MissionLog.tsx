/**
 * MissionLog — recent-captures history table for the unified capture page.
 *
 * Renders nothing pre-capture; once at least one site has been captured,
 * shows address, district, scenario, and capture time.
 */

import { formatScenarioLabel } from '../utils/formatScenario'
import type { CapturedSite } from '../hooks/useUnifiedCapture'

export interface MissionLogProps {
  capturedSites: CapturedSite[]
}

export function MissionLog({ capturedSites }: MissionLogProps) {
  if (capturedSites.length === 0) {
    return null
  }

  return (
    <section className="gps-page__captures">
      <div className="gps-panel">
        <h3>Recent captures</h3>
        <table aria-label="Recent captures">
          <thead>
            <tr>
              <th>Address</th>
              <th>District</th>
              <th>Scenario</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {capturedSites.map((site) => (
              <tr key={`${site.propertyId}-${site.capturedAt}`}>
                <td>{site.address}</td>
                <td>{site.district ?? '—'}</td>
                <td>
                  {site.scenario ? formatScenarioLabel(site.scenario) : '—'}
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
      </div>
    </section>
  )
}
