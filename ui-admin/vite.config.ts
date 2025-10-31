import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

/* eslint-disable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access */
const currentDir: string = dirname(fileURLToPath(import.meta.url))
const workspaceRoot: string = resolve(currentDir, '..')
const designTokensDir: string = resolve(workspaceRoot, 'core/design-tokens')
/* eslint-enable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access */

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    fs: {
      allow: [workspaceRoot],
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  resolve: {
    alias: {
      /* eslint-disable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call */
      '@ob/tokens': join(designTokensDir, 'index.ts'),
      '@ob/tokens.css': join(designTokensDir, 'tokens.css'),
      /* eslint-enable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call */
    },
  },
})
