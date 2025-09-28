import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

export const projectRoot = path.resolve(__dirname, '..')
const runtimeRoot = path.join(__dirname, 'runtime')

const componentMap = new Map([
  ['tests/support/appEntry.tsx', path.join(runtimeRoot, 'AppEntry.cjs')],
  [
    'tests/support/feasibilityWizardEntry.tsx',
    path.join(runtimeRoot, 'FeasibilityWizardEntry.cjs'),
  ],
])

export async function loadComponent(entryRelativePath) {
  const runtimePath = componentMap.get(entryRelativePath)
  if (!runtimePath) {
    throw new Error(`No runtime component mapped for ${entryRelativePath}`)
  }
  return import(pathToFileURL(runtimePath).href)
}

export function getGlobalI18n() {
  const instance = globalThis.__APP_I18N__
  if (!instance) {
    throw new Error('i18n instance is not initialised')
  }
  return instance
}
