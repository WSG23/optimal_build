const SCENARIO_MARKERS: Record<string, string> = {
  raw_land: 'PATH_GROUND-UP',
  en_bloc: 'PATH_ENBLOC',
  condo_redevelopment: 'PATH_CONDO',
  mixed_use: 'PATH_MIXED',
  residential: 'PATH_RESI',
  commercial: 'PATH_COMM',
  industrial: 'PATH_INDUS',
  hospitality: 'PATH_HOSP',
  retail: 'PATH_RETAIL',
  office: 'PATH_OFFICE',
  all: 'PATH_ALL',
}

export function getScenarioMarker(scenario: string): string {
  return (
    SCENARIO_MARKERS[scenario] ??
    `PATH_${scenario.toUpperCase().replace(/_/g, '')}`
  )
}

export function getSignalId(scenario: string): string {
  const marker = SCENARIO_MARKERS[scenario]
  if (marker) {
    return `FSG-${marker.replace('PATH_', '')}`
  }
  return `FSG-${scenario.toUpperCase().replace(/_/g, '').slice(0, 6)}`
}

export function calculateSignalStrength(
  opportunities: number,
  risks: number,
): number {
  return Math.min(opportunities + risks, 10)
}

export function formatTelemetryTimestamp(date = new Date()): string {
  return date.toISOString().slice(0, 19).replace('T', ' ')
}
