const { snakeCase, camelCase, joinUrl } = require('../shared.cjs')

async function fetchBuildable(input, options = {}) {
  const baseUrl = options.baseUrl ?? '/api/v1/'
  const response = await fetch(joinUrl(baseUrl, 'buildable'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(snakeCase(input)),
  })
  if (!response.ok) {
    throw new Error(`Buildable request failed with status ${response.status}`)
  }
  const payload = await response.json()
  const data = camelCase(payload)
  return {
    inputKind: data.inputKind,
    zoneCode: data.zoneCode,
    overlays: new Set(data.overlays ?? []),
    advisoryHints: new Set(data.advisoryHints ?? []),
    metrics: data.metrics ?? {},
    zoneSource: data.zoneSource ?? {},
    rules: (data.rules ?? []).map((rule) => ({
      id: rule.id,
      authority: rule.authority,
      parameterKey: rule.parameterKey,
      operator: rule.operator,
      value: rule.value,
      unit: rule.unit ?? null,
      provenance: rule.provenance ?? null,
    })),
  }
}

module.exports = { fetchBuildable }
