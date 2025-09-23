const React = require('react')
const { TranslationProvider, useTranslation } = require('./i18n/index.cjs')

function FeasibilityWizardContent() {
  const { t } = useTranslation()
  return React.createElement(
    'section',
    { className: 'feasibility-wizard' },
    React.createElement('h1', null, t('wizard.heading')),
    React.createElement(
      'p',
      null,
      'Provide project information to evaluate buildable outcomes.',
    ),
  )
}

function FeasibilityWizard() {
  return React.createElement(TranslationProvider, null, React.createElement(FeasibilityWizardContent))
}

module.exports = { FeasibilityWizard }
module.exports.default = FeasibilityWizard
