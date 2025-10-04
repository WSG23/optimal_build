const js = require('@eslint/js')
const globals = require('globals')
const tsPlugin = require('@typescript-eslint/eslint-plugin')
const tsParser = require('@typescript-eslint/parser')
const reactHooks = require('eslint-plugin-react-hooks')

if (reactHooks?.rules?.['exhaustive-deps'] && !reactHooks.rules['exhaustive-deps'].__patched) {
    const originalCreate = reactHooks.rules['exhaustive-deps'].create
    reactHooks.rules['exhaustive-deps'].create = (context) => {
        const patchedContext = new Proxy(context, {
            get(target, prop, receiver) {
                if (prop === 'getSource') {
                    return (node) => target.getSourceCode().getText(node)
                }
                return Reflect.get(target, prop, receiver)
            },
        })
        return originalCreate(patchedContext)
    }
    reactHooks.rules['exhaustive-deps'].__patched = true
}
const reactRefresh = require('eslint-plugin-react-refresh')

module.exports = [
    {
        ignores: ['dist'],
    },
    {
        files: ['**/*.{ts,tsx,js,jsx}'],
        languageOptions: {
            parser: tsParser,
            parserOptions: {
                ecmaVersion: 'latest',
                sourceType: 'module',
                ecmaFeatures: {
                    jsx: true,
                },
            },
            globals: {
                ...globals.browser,
                ...globals.node,
            },
        },
        plugins: {
            '@typescript-eslint': tsPlugin,
            'react-hooks': reactHooks,
            'react-refresh': reactRefresh,
        },
        rules: {
            ...js.configs.recommended.rules,
            ...tsPlugin.configs.recommended.rules,
            ...reactHooks.configs.recommended.rules,
            'no-undef': 'off',
            '@typescript-eslint/no-unused-vars': [
                'warn',
                {
                    args: 'after-used',
                    argsIgnorePattern: '^_',
                    varsIgnorePattern: '^_',
                    caughtErrors: 'none',
                },
            ],
            'react-refresh/only-export-components': [
                'warn',
                { allowConstantExport: true },
            ],
        },
    },
]
