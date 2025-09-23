const React = require('react')
const { useTranslation } = require('../i18n/index.cjs')

const DEFAULT_FORMATS = ['DXF', 'DWG', 'IFC', 'PDF']

function ExportDialog({ formats = DEFAULT_FORMATS, defaultOpen = false, disabled = false }) {
  const { t } = useTranslation()
  const openClass = defaultOpen ? ' export-dialog--open' : ''
  return React.createElement(
    'section',
    { className: `export-dialog${openClass}` },
    React.createElement('h3', null, t('export.heading')),
    React.createElement(
      'ul',
      null,
      formats.map((format) => React.createElement('li', { key: format }, format)),
    ),
    React.createElement(
      'div',
      { className: 'export-dialog__actions' },
      React.createElement('button', { type: 'button', disabled }, 'Download selection'),
      React.createElement('button', { type: 'button', disabled }, t('export.disabled')),
      React.createElement('button', { type: 'button', disabled }, 'Close'),
    ),
  )
}

module.exports = { ExportDialog }
