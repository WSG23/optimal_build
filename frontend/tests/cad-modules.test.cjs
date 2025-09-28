const test = require('node:test')
const assert = require('node:assert/strict')
const path = require('path')

const React = require('react')
const { renderToStaticMarkup } = require('react-dom/server')

const { loadModule } = require('./helpers/loadModule.cjs')

const { TranslationProvider } = loadModule(
    path.resolve(__dirname, '../src/i18n/index.ts'),
)
const { CadUploader } = loadModule(
    path.resolve(__dirname, '../src/modules/cad/CadUploader.tsx'),
)
const { LayerTogglePanel } = loadModule(
    path.resolve(__dirname, '../src/modules/cad/LayerTogglePanel.tsx'),
)
const { BulkReviewControls } = loadModule(
    path.resolve(__dirname, '../src/modules/cad/BulkReviewControls.tsx'),
)
const { AuditTimelinePanel } = loadModule(
    path.resolve(__dirname, '../src/modules/cad/AuditTimelinePanel.tsx'),
)
const { ExportDialog } = loadModule(
    path.resolve(__dirname, '../src/modules/cad/ExportDialog.tsx'),
)
const { RoiSummary } = loadModule(
    path.resolve(__dirname, '../src/modules/cad/RoiSummary.tsx'),
)

function renderWithProvider(element) {
    return renderToStaticMarkup(
        React.createElement(TranslationProvider, null, element),
    )
}

test('CadUploader renders detected floors and units', () => {
    const status = {
        importId: 'abc123',
        status: 'completed',
        requestedAt: '2024-03-10T10:00:00Z',
        completedAt: '2024-03-10T10:00:05Z',
        jobId: null,
        detectedFloors: [
            { name: 'Level 01', unitIds: ['01-01'] },
            { name: 'Level 02', unitIds: ['02-01'] },
        ],
        detectedUnits: ['01-01', '02-01'],
        metadata: null,
        error: null,
    }
    const summary = {
        importId: 'abc123',
        fileName: 'site.dxf',
        contentType: 'application/dxf',
        sizeBytes: 2048,
        uploadedAt: '2024-03-10T10:00:00Z',
        parseStatus: 'completed',
        detectedFloors: status.detectedFloors,
        detectedUnits: status.detectedUnits,
        vectorSummary: null,
    }
    const html = renderWithProvider(
        React.createElement(CadUploader, {
            onUpload: () => {},
            status,
            summary,
        }),
    )
    assert.match(html, /site\.dxf/)
    assert.match(html, /Level 01/)
    assert.match(html, /Level 02/)
    assert.match(html, />2</)
})

test('CadUploader falls back to dash when detection data missing', () => {
    const html = renderWithProvider(
        React.createElement(CadUploader, {
            onUpload: () => {},
            status: {
                importId: 'abc123',
                status: 'running',
                requestedAt: null,
                completedAt: null,
                jobId: null,
                detectedFloors: [],
                detectedUnits: [],
                metadata: null,
                error: null,
            },
        }),
    )
    assert.match(html, /—/)
})

test('LayerTogglePanel highlights active layers and respects disabled state', () => {
    const html = renderWithProvider(
        React.createElement(LayerTogglePanel, {
            activeLayers: ['source', 'approved'],
            onToggle: () => {},
            disabled: true,
        }),
    )
    assert.match(html, /cad-layer-toggle__button--active/)
    const disabledCount = (html.match(/disabled=""/g) || []).length
    assert.strictEqual(disabledCount >= 4, true)
})

test('BulkReviewControls disables actions when pending count is zero or locked', () => {
    const html = renderWithProvider(
        React.createElement(BulkReviewControls, {
            pendingCount: 0,
            onApproveAll: () => {},
            onRejectAll: () => {},
            disabled: true,
        }),
    )
    assert.match(html, /0/) // pending count displayed
    const disabledMatches = html.match(/disabled=""/g) || []
    assert.strictEqual(disabledMatches.length >= 2, true)
})

test('AuditTimelinePanel renders audit metadata and context summary', () => {
    const eventsHtml = renderWithProvider(
        React.createElement(AuditTimelinePanel, {
            events: [
                {
                    id: 12,
                    projectId: 5821,
                    eventType: 'overlay_decision',
                    recordedAt: '2024-01-01T00:00:00Z',
                    baselineSeconds: 900,
                    actualSeconds: 600,
                    context: { decision: 'approved', suggestion_id: 77 },
                },
            ],
        }),
    )
    assert.match(eventsHtml, /overlay_decision/)
    assert.match(eventsHtml, /Baseline: 15 min/)
    assert.match(eventsHtml, /Actual: 10 min/)
    assert.match(eventsHtml, /approved #77/)

    const emptyHtml = renderWithProvider(
        React.createElement(AuditTimelinePanel, { events: [], loading: false }),
    )
    assert.match(emptyHtml, /—/)
})

test('ExportDialog lists supported formats when opened and marks controls disabled', () => {
    const html = renderWithProvider(
        React.createElement(ExportDialog, {
            formats: undefined,
            defaultOpen: true,
            disabled: true,
        }),
    )
    assert.match(html, /DXF/)
    assert.match(html, /DWG/)
    assert.match(html, /IFC/)
    assert.match(html, /PDF/)
    const disabledMatches = html.match(/disabled=""/g) || []
    assert.ok(disabledMatches.length >= 3)
})

test('RoiSummary formats percentages and durations', () => {
    const html = renderWithProvider(
        React.createElement(RoiSummary, {
            metrics: {
                automationScore: 0.62,
                savingsPercent: 48,
                reviewHoursSaved: 14.5,
                paybackWeeks: 6,
            },
        }),
    )
    assert.match(html, /62%/)
    assert.match(html, /48%/)
    assert.match(html, /14.5h/)
    assert.match(html, /6 weeks/)
})
