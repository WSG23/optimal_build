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

function getScenarioColor(scenario: DevelopmentScenario | null): string {
  if (!scenario) return 'var(--ob-color-text-muted)'
  const s = scenario.toLowerCase()
  if (s.includes('residential')) return 'var(--ob-accent-500)'
  if (s.includes('commercial')) return 'var(--ob-brand-500)'
  if (s.includes('mixed')) return 'var(--ob-info-500)'
  if (s.includes('heritage')) return 'var(--ob-warning-500)'
  return 'var(--ob-color-text-secondary)'
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
              color: 'var(--ob-color-text-muted, #78716c)',
            }}
          >
            No prior missions.
          </p>
        ) : (
          <table style={{ color: 'var(--ob-color-text-secondary, #a8a29e)' }}>
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
                  <td
                    style={{ color: 'var(--ob-color-text-primary, #f5f5f4)' }}
                  >
                    {site.address}
                  </td>
                  <td>{site.district ?? '-'}</td>
                  <td>
                    <span
                      style={{
                        color: getScenarioColor(site.scenario),
                        fontWeight: site.scenario ? 600 : 400,
                      }}
                    >
                      {site.scenario ? formatScenarioLabel(site.scenario) : '-'}
                    </span>
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
