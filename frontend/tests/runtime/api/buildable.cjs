const { snakeCase, camelCase, joinUrl } = require('../shared.cjs')

async function postBuildable(baseUrl, input, options = {}) {
  const response = await fetch(joinUrl(baseUrl, 'buildable'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(snakeCase(input)),
    signal: options.signal,
  })
  if (!response.ok) {
    throw new Error(`Buildable request failed with status ${response.status}`)
  }
  return response.json()
}

async function fetchBuildable(input, options = {}) {
  const transport = options.transport ?? postBuildable
  const baseUrl = options.baseUrl ?? '/api/v1/'
  const payload = await transport(baseUrl, input, { signal: options.signal })
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

module.exports = { fetchBuildable, postBuildable }
