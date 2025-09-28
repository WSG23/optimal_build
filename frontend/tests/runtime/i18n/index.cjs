const React = require('react')

const translations = {
    en: {
        'app.tagline':
            'Accelerate compliance and design alignment for CAD workflows.',
        'wizard.heading': 'Feasibility assessment',
        'uploader.ready': 'Parsing complete',
        'uploader.error': 'Processing error',
        'uploader.parsing': 'Parsing drawing…',
        'uploader.dropHint': 'Drop your CAD files here',
        'uploader.browseLabel': 'Browse files',
        'uploader.latestStatus': 'Latest status',
        'uploader.floors': 'Detected floors',
        'uploader.units': 'Detected units',
        'common.fallback.dash': '—',
        'bulk.pendingLabel': 'Pending overlays',
        'bulk.approveAll': 'Approve all',
        'bulk.rejectAll': 'Reject all',
        'audit.heading': 'Audit timeline',
        'audit.empty': '—',
        'audit.baseline': 'Baseline',
        'audit.actual': 'Actual',
        'export.heading': 'Export formats',
        'export.disabled': 'Downloads unavailable',
        'roi.heading': 'Return on investment',
        'roi.automationScore': 'Automation score',
        'roi.savingsPercent': 'Savings',
        'roi.reviewHoursSaved': 'Review hours saved',
        'roi.paybackWeeks': 'Payback period',
    },
    ja: {
        'app.tagline':
            'CAD ワークフローのコンプライアンスと設計調整を加速します。',
        'wizard.heading': '実現可能性評価',
    },
}

const supportedLanguages = [
    { value: 'en', label: 'English' },
    { value: 'ja', label: '日本語' },
]

const listeners = new Set()

const i18n = {
    language: 'en',
    async changeLanguage(language) {
        const next = translations[language] ? language : 'en'
        i18n.language = next
        listeners.forEach((listener) => listener(next))
        return next
    },
    t(key) {
        const table = translations[i18n.language] ?? translations.en
        return table[key] ?? translations.en[key] ?? key
    },
    subscribe(listener) {
        listeners.add(listener)
        return () => listeners.delete(listener)
    },
    get resources() {
        return translations
    },
}

globalThis.__APP_I18N__ = i18n

const I18nContext = React.createContext(i18n)

function TranslationProvider({ children }) {
    return React.createElement(I18nContext.Provider, { value: i18n, children })
}

function useTranslation() {
    const instance = React.useContext(I18nContext)
    const translate = (key) => {
        const table = translations[instance.language] ?? translations.en
        return table[key] ?? translations.en[key] ?? key
    }
    return { t: translate, i18n: instance }
}

module.exports = {
    TranslationProvider,
    useTranslation,
    supportedLanguages,
    i18n,
}
