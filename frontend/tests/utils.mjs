import fs from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

import { build } from 'esbuild'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
export const projectRoot = path.resolve(__dirname, '..')

export async function loadComponent(entryRelativePath) {
  const entryPoint = path.join(projectRoot, entryRelativePath)
  const result = await build({
    entryPoints: [entryPoint],
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
      '.json': 'json',
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
  const tempFile = path.join(tempDir, `${path.basename(entryRelativePath)}.bundle.mjs`)

  try {
    await fs.writeFile(tempFile, output.text, 'utf8')
    return await import(pathToFileURL(tempFile).href)
  } finally {
    await fs.rm(tempDir, { recursive: true, force: true })
  }
}

export function getGlobalI18n() {
  const instance = globalThis.__APP_I18N__
  if (!instance) {
    throw new Error('i18n instance is not initialised')
  }
  return instance
}
