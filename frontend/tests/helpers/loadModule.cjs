const path = require('node:path')

const runtimeRoot = path.resolve(__dirname, '..', 'runtime')

const moduleMap = new Map([
  [path.resolve(__dirname, '../../src/api/client.ts'), path.join(runtimeRoot, 'api', 'client.cjs')],
  [path.resolve(__dirname, '../../src/api/buildable.ts'), path.join(runtimeRoot, 'api', 'buildable.cjs')],
  [path.resolve(__dirname, '../../src/api/finance.ts'), path.join(runtimeRoot, 'api', 'finance.cjs')],
  [
    path.resolve(__dirname, '../../src/mocks/buildable.ts'),
    path.join(runtimeRoot, 'mocks', 'buildable.cjs'),
  ],
  [path.resolve(__dirname, '../../src/i18n/index.ts'), path.join(runtimeRoot, 'i18n', 'index.cjs')],
  [path.resolve(__dirname, '../../src/modules/cad/CadUploader.tsx'), path.join(runtimeRoot, 'cad', 'CadUploader.cjs')],
  [path.resolve(__dirname, '../../src/modules/cad/LayerTogglePanel.tsx'), path.join(runtimeRoot, 'cad', 'LayerTogglePanel.cjs')],
  [path.resolve(__dirname, '../../src/modules/cad/BulkReviewControls.tsx'), path.join(runtimeRoot, 'cad', 'BulkReviewControls.cjs')],
  [path.resolve(__dirname, '../../src/modules/cad/AuditTimelinePanel.tsx'), path.join(runtimeRoot, 'cad', 'AuditTimelinePanel.cjs')],
  [path.resolve(__dirname, '../../src/modules/cad/ExportDialog.tsx'), path.join(runtimeRoot, 'cad', 'ExportDialog.cjs')],
  [path.resolve(__dirname, '../../src/modules/cad/RoiSummary.tsx'), path.join(runtimeRoot, 'cad', 'RoiSummary.cjs')],
  [path.resolve(__dirname, '../../src/modules/cad/layerToggle.ts'), path.join(runtimeRoot, 'cad', 'LayerTogglePanel.cjs')],
  [path.resolve(__dirname, '../../src/router.tsx'), path.join(runtimeRoot, 'router.cjs')],
])

function loadModule(modulePath) {
  const absPath = path.resolve(modulePath)
  const target = moduleMap.get(absPath)
  if (!target) {
    throw new Error(`No runtime module mapped for ${absPath}`)
  }
  // eslint-disable-next-line global-require, import/no-dynamic-require
  return require(target)
}

module.exports = { loadModule }
