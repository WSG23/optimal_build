const path = require('node:path')
const { createRequire } = require('node:module')

const candidateManifests = [
  path.join(__dirname, 'frontend', 'package.json'),
  path.join(__dirname, 'ui-admin', 'package.json'),
]

const candidateRequires = [require]
for (const manifest of candidateManifests) {
  try {
    candidateRequires.push(createRequire(manifest))
  } catch (error) {
    if (error?.code !== 'ERR_INVALID_ARG_VALUE') {
      throw error
    }
  }
}

const requireFromAny = (id) => {
  let lastError
  for (const loader of candidateRequires) {
    try {
      return loader(id)
    } catch (error) {
      if (error?.code !== 'MODULE_NOT_FOUND') {
        throw error
      }
      lastError = error
    }
  }
  throw lastError
}

const js = requireFromAny('@eslint/js')
const globals = requireFromAny('globals')
const tseslint = requireFromAny('@typescript-eslint/eslint-plugin')
const tsParser = requireFromAny('@typescript-eslint/parser')
const reactHooks = requireFromAny('eslint-plugin-react-hooks')
const reactRefresh = requireFromAny('eslint-plugin-react-refresh')

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

const sharedReactConfig = (baseDir) => {
  const baseFilesGlob = `${baseDir}/**/*`
  const sharedGlobals = {
    ...globals.browser,
    ...globals.es2021,
    ...globals.node,
  }

  return [
    {
      files: [`${baseFilesGlob}.{ts,tsx}`],
      ignores: [`${baseDir}/dist/**`],
      languageOptions: {
        parser: tsParser,
        parserOptions: {
          project: path.join(__dirname, baseDir, 'tsconfig.json'),
          tsconfigRootDir: __dirname,
          ecmaVersion: 'latest',
          sourceType: 'module',
        },
        globals: sharedGlobals,
      },
      plugins: {
        '@typescript-eslint': tseslint,
        'react-hooks': reactHooks,
        'react-refresh': reactRefresh,
      },
      rules: {
        ...js.configs.recommended.rules,
        ...tseslint.configs['recommended-type-checked'].rules,
        ...tseslint.configs['strict-type-checked'].rules,
        ...reactHooks.configs.recommended.rules,
        'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
      },
    },
    {
      files: [`${baseFilesGlob}.{js,jsx,cjs,mjs}`],
      ignores: [`${baseDir}/dist/**`],
      languageOptions: {
        parserOptions: {
          ecmaVersion: 'latest',
          sourceType: 'module',
        },
        globals: sharedGlobals,
      },
      plugins: {
        'react-hooks': reactHooks,
        'react-refresh': reactRefresh,
      },
      rules: {
        ...js.configs.recommended.rules,
        ...reactHooks.configs.recommended.rules,
        'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
      },
    },
  ]
}

module.exports = [
  {
    ignores: ['node_modules/**'],
    linterOptions: {
      reportUnusedDisableDirectives: false,
    },
  },
  ...sharedReactConfig('frontend'),
  ...sharedReactConfig('ui-admin'),
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
