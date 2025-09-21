import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'
import test from 'node:test'

import { build } from 'esbuild'
import React from 'react'
import { renderToString } from 'react-dom/server'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const projectRoot = path.resolve(__dirname, '..')

async function loadAppComponent() {
  const result = await build({
    entryPoints: [path.join(projectRoot, 'src', 'App.tsx')],
    absWorkingDir: projectRoot,
    bundle: true,
    format: 'esm',
    platform: 'node',
    write: false,
    jsx: 'automatic',
    jsxImportSource: 'react',
    logLevel: 'silent',
    external: ['react', 'react-dom', 'react/jsx-runtime'],
    loader: {
      '.ts': 'ts',
      '.tsx': 'tsx',
    },
    define: {
      'import.meta.env.VITE_API_BASE_URL': 'undefined',
      'import.meta.env': '{}',
    },
  })

  if (!result.outputFiles || result.outputFiles.length === 0) {
    throw new Error('esbuild did not produce any output files')
  }

  const [output] = result.outputFiles
  const tempDir = await fs.mkdtemp(path.join(projectRoot, '.tmp-e2e-'))
  const tempFile = path.join(tempDir, 'App.bundle.mjs')

  try {
    await fs.writeFile(tempFile, output.text, 'utf8')
    const module = await import(pathToFileURL(tempFile).href)

    if (!module.default) {
      throw new Error('App component was not exported as default')
    }

    return module.default
  } finally {
    await fs.rm(tempDir, { recursive: true, force: true })
  }
}

test('App renders the expected headline', async () => {
  const App = await loadAppComponent()
  const html = renderToString(React.createElement(App))
  assert.match(
    html,
    /<h1[^>]*>\s*Optimal Build Studio\s*<\/h1>/i,
    'Expected heading to contain "Optimal Build Studio"',
  )
})
