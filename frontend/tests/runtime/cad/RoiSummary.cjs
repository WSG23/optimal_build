const React = require('react')
const { useTranslation } = require('../i18n/index.cjs')

function formatPercent(value) {
    if (value === undefined || value === null) {
        return '—'
    }
    if (value <= 1) {
        return `${Math.round(value * 100)}%`
    }
    return `${value}%`
}

function RoiSummary({ metrics = {} }) {
    const { t } = useTranslation()
    return React.createElement(
        'section',
        { className: 'roi-summary' },
        React.createElement('h3', null, t('roi.heading')),
        React.createElement(
            'ul',
            null,
            React.createElement(
                'li',
                null,
                `${t('roi.automationScore')}: ${formatPercent(
                    metrics.automationScore,
                )}`,
            ),
            React.createElement(
                'li',
                null,
                `${t('roi.savingsPercent')}: ${formatPercent(
                    metrics.savingsPercent,
                )}`,
            ),
            React.createElement(
                'li',
                null,
                `${t('roi.reviewHoursSaved')}: ${
                    metrics.reviewHoursSaved ?? '—'
                }h`,
            ),
            React.createElement(
                'li',
                null,
                `${t('roi.paybackWeeks')}: ${
                    metrics.paybackWeeks ?? '—'
                } weeks`,
            ),
        ),
    )
}

module.exports = { RoiSummary }
