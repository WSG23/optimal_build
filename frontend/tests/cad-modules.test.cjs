const test = require('node:test')
const assert = require('node:assert/strict')
const path = require('path')

const React = require('react')
const { renderToStaticMarkup } = require('react-dom/server')

const { loadModule } = require('./helpers/loadModule.cjs')

const { TranslationProvider } = loadModule(path.resolve(__dirname, '../src/i18n/index.tsx'))
const { CadUploader } = loadModule(path.resolve(__dirname, '../src/modules/cad/CadUploader.tsx'))
const { LayerTogglePanel } = loadModule(path.resolve(__dirname, '../src/modules/cad/LayerTogglePanel.tsx'))
const { BulkReviewControls } = loadModule(path.resolve(__dirname, '../src/modules/cad/BulkReviewControls.tsx'))
const { AuditTimelinePanel } = loadModule(path.resolve(__dirname, '../src/modules/cad/AuditTimelinePanel.tsx'))
const { ExportDialog } = loadModule(path.resolve(__dirname, '../src/modules/cad/ExportDialog.tsx'))
const { RoiSummary } = loadModule(path.resolve(__dirname, '../src/modules/cad/RoiSummary.tsx'))

function renderWithProvider(element) {
  return renderToStaticMarkup(React.createElement(TranslationProvider, null, element))
}

test('CadUploader renders parse status and overlay metadata', () => {
  const status = {
    status: 'ready',
    overlays: ['heritage_conservation', 'coastal_protection'],
    hints: ['Submit heritage impact assessment'],
    zoneCode: 'RA',
    message: 'Parse completed',
  }
  const html = renderWithProvider(React.createElement(CadUploader, {
    onUpload: () => {},
    status,
    zoneCode: 'RA',
  }))
  assert.match(html, /Parse completed/)
  assert.match(html, /heritage_conservation/)
  assert.match(html, /Submit heritage impact assessment/)
  assert.match(html, /<dd>RA<\/dd>/)
})

test('CadUploader falls back to dash when zone metadata missing', () => {
  const html = renderWithProvider(React.createElement(CadUploader, {
    onUpload: () => {},
    status: {
      status: 'processing',
      overlays: [],
      hints: [],
      zoneCode: null,
      message: null,
    },
  }))
  assert.match(html, /—/)
})

test('LayerTogglePanel highlights active layers and respects disabled state', () => {
  const html = renderWithProvider(React.createElement(LayerTogglePanel, {
    activeLayers: ['source', 'approved'],
    onToggle: () => {},
    disabled: true,
  }))
  assert.match(html, /cad-layer-toggle__button--active/)
  const disabledCount = (html.match(/disabled=""/g) || []).length
  assert.strictEqual(disabledCount >= 4, true)
})

test('BulkReviewControls disables actions when pending count is zero or locked', () => {
  const html = renderWithProvider(React.createElement(BulkReviewControls, {
    pendingCount: 0,
    onApproveAll: () => {},
    onRejectAll: () => {},
    disabled: true,
  }))
  assert.match(html, /0 Pending/)
  const disabledMatches = html.match(/disabled=""/g) || []
  assert.strictEqual(disabledMatches.length >= 2, true)
})

test('AuditTimelinePanel renders entries and fallback', () => {
  const eventsHtml = renderWithProvider(React.createElement(AuditTimelinePanel, {
    events: [
      { ruleId: 12, baseline: 'Baseline saved', updated: '2024-01-01' },
      { ruleId: 13, baseline: 'Decision approved', updated: '2024-02-10' },
    ],
  }))
  assert.match(eventsHtml, /#12/)
  assert.match(eventsHtml, /Decision approved/)

  const emptyHtml = renderWithProvider(React.createElement(AuditTimelinePanel, {
    events: [],
    loading: false,
  }))
  assert.match(emptyHtml, /—/)
})

test('ExportDialog lists formats when opened and marks controls disabled', () => {
  const html = renderWithProvider(React.createElement(ExportDialog, {
    formats: ['DXF', 'PDF'],
    defaultOpen: true,
    disabled: true,
  }))
  assert.match(html, /Export options/)
  assert.match(html, /DXF/)
  assert.match(html, /PDF/)
  const disabledMatches = html.match(/disabled=""/g) || []
  assert.ok(disabledMatches.length >= 3)
})

test('RoiSummary formats percentages and durations', () => {
  const html = renderWithProvider(React.createElement(RoiSummary, {
    metrics: {
      automationScore: 0.62,
      savingsPercent: 48,
      reviewHoursSaved: 14.5,
      paybackWeeks: 6,
    },
  }))
  assert.match(html, /62%/)
  assert.match(html, /48%/)
  assert.match(html, /14.5h/)
  assert.match(html, /6 weeks/)
})
