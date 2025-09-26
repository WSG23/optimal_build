const { snakeCase, camelCase, joinUrl } = require('../shared.cjs')

async function runFinanceFeasibility(request, options = {}) {
  const baseUrl = options.baseUrl ?? '/api/v1/'
  const response = await fetch(joinUrl(baseUrl, 'finance/feasibility'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Role': 'admin',
    },
    body: JSON.stringify(snakeCase(request)),
  })
  if (!response.ok) {
    throw new Error(`Finance feasibility request failed with status ${response.status}`)
  }
  const payload = await response.json()
  const data = camelCase(payload)
  return {
    scenarioId: data.scenarioId,
    projectId: data.projectId,
    finProjectId: data.finProjectId,
    scenarioName: data.scenarioName,
    currency: data.currency,
    escalatedCost: data.escalatedCost,
    costIndex: data.costIndex ?? null,
    results: data.results ?? [],
    dscrTimeline: data.dscrTimeline ?? [],
  }
}

module.exports = { runFinanceFeasibility }
