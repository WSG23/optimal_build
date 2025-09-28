const {
    snakeCase,
    camelCase,
    joinUrl,
    normaliseBaseUrl,
} = require('../shared.cjs')

function mapCadImportSummary(payload) {
    const data = camelCase(payload)
    return {
        importId: data.importId,
        fileName: data.filename ?? data.fileName,
        contentType: data.contentType,
        sizeBytes: data.sizeBytes,
        vectorSummary: data.vectorSummary ?? null,
        uploadedAt: data.uploadedAt,
        parseStatus: data.parseStatus,
        detectedFloors: (data.detectedFloors ?? []).map((floor) => ({
            name: floor.name,
            unitIds: floor.unitIds ?? [],
        })),
        detectedUnits: data.detectedUnits ?? [],
    }
}

function mapParseStatusUpdate(payload) {
    const data = camelCase(payload)
    const result = data.result ?? {}
    const detectedFloors = result.detectedFloors ?? []
    const detectedUnits = result.detectedUnits ?? []
    return {
        importId: data.importId,
        status: data.status,
        requestedAt: data.requestedAt ?? null,
        completedAt: data.completedAt ?? null,
        jobId: data.jobId ?? null,
        error: data.error ?? null,
        detectedFloors: detectedFloors.map((floor) => ({
            name: floor.name,
            unitIds: floor.unitIds ?? [],
        })),
        detectedUnits,
    }
}

function mapOverlaySuggestion(payload) {
    const data = camelCase(payload)
    return {
        id: data.id,
        projectId: data.projectId,
        sourceGeometryId: data.sourceGeometryId,
        code: data.code,
        title: data.title,
        rationale: data.rationale,
        severity: data.severity,
        status: data.status,
        engineVersion: data.engineVersion,
        enginePayload: data.enginePayload ?? {},
        score: data.score ?? null,
        geometryChecksum: data.geometryChecksum ?? null,
        createdAt: data.createdAt,
        updatedAt: data.updatedAt,
        decidedAt: data.decidedAt ?? null,
        decidedBy: data.decidedBy ?? null,
        decisionNotes: data.decisionNotes ?? null,
        decision: data.decision ?? null,
    }
}

class ApiClient {
    constructor(baseUrl = '/api/v1/') {
        this.baseUrl = normaliseBaseUrl(baseUrl)
    }

    async uploadCadDrawing(file) {
        const formData = new FormData()
        formData.append('file', file)
        const response = await fetch(joinUrl(this.baseUrl, 'cad/imports'), {
            method: 'POST',
            body: formData,
        })
        if (!response.ok) {
            throw new Error(`Upload failed with status ${response.status}`)
        }
        const payload = await response.json()
        return mapCadImportSummary(payload)
    }

    pollParseStatus({
        importId,
        onUpdate,
        intervalMs = 1000,
        timeoutMs = 60000,
    }) {
        const url = joinUrl(this.baseUrl, `cad/imports/${importId}`)
        let cancelled = false
        const deadline = Date.now() + timeoutMs
        let timer = null

        const tick = async () => {
            if (cancelled) {
                return
            }
            try {
                const response = await fetch(url)
                if (!response.ok) {
                    throw new Error(
                        `Status request failed with ${response.status}`,
                    )
                }
                const payload = await response.json()
                const update = mapParseStatusUpdate(payload)
                onUpdate(update)
                if (
                    update.status === 'completed' ||
                    update.status === 'failed' ||
                    Date.now() >= deadline
                ) {
                    cancelled = true
                    return
                }
            } catch (error) {
                onUpdate({ importId, status: 'error', error: error.message })
                cancelled = true
                return
            }
            if (!cancelled) {
                timer = setTimeout(tick, intervalMs)
            }
        }

        tick()

        return () => {
            cancelled = true
            if (timer) {
                clearTimeout(timer)
            }
        }
    }

    async decideOverlay(projectId, { suggestionId, decision }) {
        const response = await fetch(
            joinUrl(
                this.baseUrl,
                `projects/${projectId}/overlays/${suggestionId}`,
            ),
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(snakeCase({ decision })),
            },
        )
        if (!response.ok) {
            throw new Error(
                `Overlay decision failed with status ${response.status}`,
            )
        }
        const payload = await response.json()
        const item = payload.item ?? payload
        return mapOverlaySuggestion(item)
    }

    async listRules() {
        const response = await fetch(joinUrl(this.baseUrl, 'rules'))
        if (!response.ok) {
            throw new Error(
                `Failed to list rules with status ${response.status}`,
            )
        }
        const payload = await response.json()
        return (payload.rules ?? payload ?? []).map((rule) => camelCase(rule))
    }

    async getDefaultPipelineSuggestions({ overlays = [], hints = [] }) {
        const rules = await this.listRules()
        const overlaySet = new Set(overlays)
        const hintSet = new Set(hints.map((hint) => hint.toLowerCase()))

        const suggestions = []
        for (const rule of rules) {
            const ruleOverlays = rule.overlays ?? []
            const ruleHints = rule.advisoryHints ?? []
            const matchesOverlay = ruleOverlays.some((overlay) =>
                overlaySet.has(overlay),
            )
            const matchesHint = ruleHints.some((hint) =>
                hintSet.has(hint.toLowerCase()),
            )
            if (!matchesOverlay && !matchesHint) {
                continue
            }
            const focus = rule.topic ?? rule.parameterKey ?? 'rule'
            suggestions.push({
                id: `suggestion-${rule.id}`,
                focus,
                overlays: ruleOverlays,
                hints: ruleHints,
                relatedRuleIds: [rule.id],
                priority: matchesOverlay ? 1 : 0,
            })
        }

        suggestions.sort((a, b) => b.priority - a.priority)
        return suggestions
    }
}

module.exports = { ApiClient }
