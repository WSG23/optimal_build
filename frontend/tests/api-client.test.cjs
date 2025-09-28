const test = require('node:test')
const assert = require('node:assert/strict')
const path = require('path')

const { loadModule } = require('./helpers/loadModule.cjs')

if (typeof global.FormData === 'undefined') {
    global.FormData = class FormDataStub {
        constructor() {
            this._entries = []
        }

        append(...args) {
            this._entries.push(args)
        }
    }
}

const { ApiClient } = loadModule(
    path.resolve(__dirname, '../src/api/client.ts'),
)

function restoreFetch(originalFetch) {
    if (originalFetch) {
        global.fetch = originalFetch
    } else {
        delete global.fetch
    }
}

test('uploadCadDrawing maps import summary fields', async () => {
    const originalFetch = global.fetch
    const calls = []
    global.fetch = async (input, init) => {
        calls.push({ input, init })
        return new Response(
            JSON.stringify({
                import_id: 'abc123',
                filename: 'site.dxf',
                content_type: 'application/dxf',
                size_bytes: 2048,
                storage_path: 's3://bucket/site.dxf',
                vector_storage_path: null,
                uploaded_at: '2024-03-10T10:00:00Z',
                layer_metadata: [],
                detected_floors: [{ name: 'Level 01', unit_ids: ['01-01'] }],
                detected_units: ['01-01'],
                vector_summary: null,
                parse_status: 'pending',
            }),
            { status: 201, headers: { 'Content-Type': 'application/json' } },
        )
    }

    const client = new ApiClient('http://example.com/')
    const file = new File(['content'], 'site.dxf', { type: 'application/dxf' })
    const summary = await client.uploadCadDrawing(file)

    restoreFetch(originalFetch)

    assert.strictEqual(summary.importId, 'abc123')
    assert.strictEqual(summary.fileName, 'site.dxf')
    assert.strictEqual(summary.parseStatus, 'pending')
    assert.deepEqual(
        summary.detectedFloors.map((floor) => floor.name),
        ['Level 01'],
    )
    assert.deepEqual(summary.detectedFloors[0].unitIds, ['01-01'])
    assert.deepEqual(summary.detectedUnits, ['01-01'])
    assert.ok(typeof calls[0].init.body.append === 'function')
})

test('pollParseStatus stops after completion update', async () => {
    const originalFetch = global.fetch
    let call = 0
    global.fetch = async () => {
        call += 1
        const payloads = [
            {
                import_id: 'abc123',
                status: 'running',
                requested_at: '2024-03-10T10:00:00Z',
                completed_at: null,
                result: { detected_floors: [], detected_units: [] },
                error: null,
                job_id: null,
            },
            {
                import_id: 'abc123',
                status: 'completed',
                requested_at: '2024-03-10T10:00:00Z',
                completed_at: '2024-03-10T10:00:05Z',
                result: {
                    detected_floors: [
                        { name: 'Level 01', unit_ids: ['01-01'] },
                    ],
                    detected_units: ['01-01'],
                },
                error: null,
                job_id: null,
            },
        ]
        const payload = payloads[Math.min(call - 1, payloads.length - 1)]
        return new Response(JSON.stringify(payload), { status: 200 })
    }

    const client = new ApiClient('http://example.com/')
    const updates = []
    const cancel = client.pollParseStatus({
        importId: 'abc123',
        onUpdate: (update) => updates.push(update),
        intervalMs: 5,
        timeoutMs: 100,
    })

    await new Promise((resolve) => setTimeout(resolve, 30))
    cancel()
    restoreFetch(originalFetch)

    assert.ok(updates.length >= 2)
    const finalUpdate = updates.at(-1)
    assert.strictEqual(finalUpdate.status, 'completed')
    assert.deepEqual(finalUpdate.detectedUnits, ['01-01'])
})

test('decideOverlay normalises overlay suggestion payload', async () => {
    const originalFetch = global.fetch
    global.fetch = async () =>
        new Response(
            JSON.stringify({
                item: {
                    id: 99,
                    project_id: 5821,
                    source_geometry_id: 10,
                    code: 'heritage_conservation',
                    title: 'Heritage conservation review',
                    rationale: 'Site flagged as heritage.',
                    severity: 'high',
                    status: 'approved',
                    engine_version: '1.0.0',
                    engine_payload: { triggers: ['heritage_zone'] },
                    score: 0.9,
                    geometry_checksum: 'abc',
                    created_at: '2024-03-10T10:00:00Z',
                    updated_at: '2024-03-10T10:05:00Z',
                    decided_at: '2024-03-10T10:05:00Z',
                    decided_by: 'Planner',
                    decision_notes: 'Approved after review.',
                    decision: {
                        id: 201,
                        decision: 'approved',
                        decided_by: 'Planner',
                        decided_at: '2024-03-10T10:05:00Z',
                        notes: 'Approved after review.',
                    },
                },
            }),
            { status: 200, headers: { 'Content-Type': 'application/json' } },
        )

    const client = new ApiClient('http://example.com/')
    const suggestion = await client.decideOverlay(5821, {
        suggestionId: 99,
        decision: 'approved',
    })

    restoreFetch(originalFetch)

    assert.strictEqual(suggestion.id, 99)
    assert.strictEqual(suggestion.status, 'approved')
    assert.strictEqual(suggestion.decision?.decision, 'approved')
    assert.deepEqual(suggestion.enginePayload, { triggers: ['heritage_zone'] })
})

test('getDefaultPipelineSuggestions prioritises overlay matches', async () => {
    const client = new ApiClient('http://example.com/')
    client.listRules = async () => [
        {
            id: 1,
            parameterKey: 'fire.width',
            operator: '>=',
            value: '4.5',
            unit: 'm',
            authority: 'SCDF',
            topic: 'Fire safety',
            reviewStatus: 'approved',
            overlays: ['fire_access'],
            advisoryHints: ['Ensure access clearance'],
            normalized: [],
        },
        {
            id: 2,
            parameterKey: 'zoning.plot_ratio',
            operator: '<=',
            value: '3.5',
            unit: null,
            authority: 'URA',
            topic: 'Zoning',
            reviewStatus: 'approved',
            overlays: ['coastal'],
            advisoryHints: [],
            normalized: [],
        },
    ]

    const suggestions = await client.getDefaultPipelineSuggestions({
        overlays: ['fire_access'],
        hints: [],
    })
    assert.ok(suggestions.length > 0)
    assert.strictEqual(suggestions[0].relatedRuleIds.includes(1), true)
    assert.ok(suggestions[0].focus.toLowerCase().includes('fire'))
})
