const js = require('@eslint/js')
const globals = require('globals')
const tseslint = require('@typescript-eslint/eslint-plugin')
const tsParser = require('@typescript-eslint/parser')
const reactHooks = require('eslint-plugin-react-hooks')
const reactRefresh = require('eslint-plugin-react-refresh')

const sharedReactTsConfig = (baseDir) => ({
  files: [`${baseDir}/**/*.{ts,tsx,js,jsx,cjs,mjs}`],
  ignores: [`${baseDir}/dist/**`],
  languageOptions: {
    parser: tsParser,
    parserOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
    },
    globals: {
      ...globals.browser,
      ...globals.es2021,
      ...globals.node,
    },
  },
  plugins: {
    '@typescript-eslint': tseslint,
    'react-hooks': reactHooks,
    'react-refresh': reactRefresh,
  },
  rules: {
    ...js.configs.recommended.rules,
    ...tseslint.configs.recommended.rules,
    ...reactHooks.configs.recommended.rules,
    'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
  },
})

module.exports = [
  {
    ignores: ['node_modules/**'],
    linterOptions: {
      reportUnusedDisableDirectives: false,
    },
  },
  sharedReactTsConfig('frontend'),
  sharedReactTsConfig('ui-admin'),
  {
    files: [
      'frontend/**/*.cjs',
      'frontend/**/*.js',
      'ui-admin/**/*.cjs',
      'ui-admin/**/*.js',
    ],
    languageOptions: {
      sourceType: 'commonjs',
    },
    rules: {
      '@typescript-eslint/no-require-imports': 'off',
    },
  },
]
