const React = require('react')
const { TranslationProvider, useTranslation } = require('./i18n/index.cjs')

function AppShell() {
  const { t } = useTranslation()
  return React.createElement(
    'main',
    { className: 'app-shell' },
    React.createElement('h1', null, 'Optimal Build Studio'),
    React.createElement('p', { className: 'app-tagline' }, t('app.tagline')),
  )
}

function App() {
  return React.createElement(
    TranslationProvider,
    null,
    React.createElement(AppShell),
  )
}

module.exports = { App }
module.exports.default = App
