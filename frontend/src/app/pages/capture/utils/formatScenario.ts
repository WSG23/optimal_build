import type { DevelopmentScenario } from '../../../../api/agents'

/** Human-readable label for a development scenario value. */
export function formatScenarioLabel(value: DevelopmentScenario): string {
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
