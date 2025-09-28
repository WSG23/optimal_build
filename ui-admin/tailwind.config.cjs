const withOpacityValue =
    (cssVariable) =>
    ({ opacityValue }) => {
        if (opacityValue === undefined) {
            return `rgb(var(${cssVariable}))`
        }
        return `rgb(var(${cssVariable}) / ${opacityValue})`
    }

module.exports = {
    content: ['./index.html', './src/**/*.{ts,tsx}'],
    theme: {
        extend: {
            colors: {
                surface: {
                    DEFAULT: 'var(--ob-color-surface-default)',
                    alt: 'var(--ob-color-surface-alt)',
                    inverse: withOpacityValue('--ob-color-surface-inverse-rgb'),
                },
                text: {
                    primary: withOpacityValue('--ob-color-text-primary-rgb'),
                    muted: withOpacityValue('--ob-color-text-muted-rgb'),
                    inverse: withOpacityValue('--ob-color-text-inverse-rgb'),
                    'inverse-muted': withOpacityValue(
                        '--ob-color-text-inverse-muted-rgb',
                    ),
                },
                brand: {
                    primary: withOpacityValue('--ob-color-brand-primary-rgb'),
                    'primary-emphasis': withOpacityValue(
                        '--ob-color-brand-primary-emphasis-rgb',
                    ),
                    soft: withOpacityValue('--ob-color-brand-soft-rgb'),
                },
                border: {
                    subtle: withOpacityValue('--ob-color-border-subtle-rgb'),
                    neutral: withOpacityValue('--ob-color-border-neutral-rgb'),
                },
                info: {
                    strong: withOpacityValue('--ob-color-info-strong-rgb'),
                },
                success: {
                    strong: withOpacityValue('--ob-color-success-strong-rgb'),
                },
                warning: {
                    strong: withOpacityValue('--ob-color-warning-strong-rgb'),
                    soft: 'var(--ob-color-warning-soft)',
                },
                error: {
                    strong: withOpacityValue('--ob-color-error-strong-rgb'),
                    muted: withOpacityValue('--ob-color-error-muted-rgb'),
                    soft: withOpacityValue('--ob-color-error-soft-rgb'),
                },
            },
            borderRadius: {
                md: 'var(--ob-radius-md)',
                lg: 'var(--ob-radius-lg)',
                xl: 'var(--ob-radius-xl)',
                '2xl': 'var(--ob-radius-2xl)',
                pill: 'var(--ob-radius-pill)',
            },
            fontWeight: {
                regular: 'var(--ob-font-weight-regular)',
                semibold: 'var(--ob-font-weight-semibold)',
                bold: 'var(--ob-font-weight-bold)',
            },
        },
    },
    plugins: [],
}
