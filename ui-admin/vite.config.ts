import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

/* eslint-disable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access */
const currentDir: string = dirname(fileURLToPath(import.meta.url))
const workspaceRoot: string = resolve(currentDir, '..')
const designTokensDir: string = resolve(workspaceRoot, 'core/design-tokens')
/* eslint-enable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access */

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, currentDir, '')
  const backendPort = (env.BACKEND_PORT || '').trim() || '8000'
  const proxyTarget = `http://127.0.0.1:${backendPort}`

  return {
    plugins: [react()],
    server: {
      port: 5173,
      fs: {
        allow: [workspaceRoot],
      },
      proxy: {
        '/api': {
          target: proxyTarget,
          changeOrigin: true,
          ws: true,
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
  }
})
