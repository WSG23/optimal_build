const React = require('react')
const { useTranslation } = require('../i18n/index.cjs')

function formatMinutes(seconds) {
  if (typeof seconds !== 'number' || Number.isNaN(seconds)) {
    return '—'
  }
  const minutes = Math.round(seconds / 60)
  return `${minutes} min`
}

function renderContextSummary(context) {
  if (!context) {
    return null
  }
  if (context.decision && context.suggestion_id) {
    return `${context.decision} #${context.suggestion_id}`
  }
  return Object.entries(context)
    .map(([key, value]) => `${key}: ${value}`)
    .join(', ')
}

function AuditTimelinePanel({ events = [], loading = false }) {
  const { t } = useTranslation()
  if (loading) {
    return React.createElement(
      'div',
      { className: 'audit-timeline audit-timeline--loading' },
      '…',
    )
  }
  if (!events.length) {
    return React.createElement(
      'div',
      { className: 'audit-timeline audit-timeline--empty' },
      t('audit.empty'),
    )
  }
  return React.createElement(
    'section',
    { className: 'audit-timeline' },
    React.createElement('h3', null, t('audit.heading')),
    React.createElement(
      'ul',
      null,
      events.map((event) =>
        React.createElement(
          'li',
          { key: event.id },
          React.createElement(
            'span',
            { className: 'audit-timeline__type' },
            event.eventType,
          ),
          React.createElement(
            'span',
            null,
            `${t('audit.baseline')}: ${formatMinutes(event.baselineSeconds)}`,
          ),
          React.createElement(
            'span',
            null,
            `${t('audit.actual')}: ${formatMinutes(event.actualSeconds)}`,
          ),
          event.context
            ? React.createElement(
                'span',
                { className: 'audit-timeline__context' },
                renderContextSummary(event.context),
              )
            : null,
        ),
      ),
    ),
  )
}

module.exports = { AuditTimelinePanel }
