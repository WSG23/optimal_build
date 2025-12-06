import path from 'node:path'

import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  const serverPort = Number.parseInt(env.FRONTEND_PORT ?? '', 10)
  const host = env.VITE_DEV_HOST?.trim() || '127.0.0.1'

  const rawApiBase =
    env.VITE_API_BASE_URL?.trim() || env.VITE_API_BASE?.trim() || ''
  const backendPort = env.BACKEND_PORT?.trim() || '8000'
  const resolvedApiBase =
    rawApiBase.length > 0 && rawApiBase !== '/'
      ? rawApiBase
      : `http://127.0.0.1:${backendPort}`
  const proxyTarget = resolvedApiBase.replace(/\/+$/, '')

  console.log('[vite.config] BACKEND_PORT:', backendPort)
  console.log('[vite.config] Proxy target:', proxyTarget)

  return {
    plugins: [react()],
    server: {
      port: Number.isFinite(serverPort) ? serverPort : 3000,
      host,
      fs: {
        allow: [path.resolve(__dirname, '..')],
      },
      proxy: {
        '/api': {
          target: proxyTarget,
          changeOrigin: true,
        },
        '/static': {
          target: proxyTarget,
          changeOrigin: true,
        },
      },
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
        '@ob/tokens': path.resolve(__dirname, '../core/design-tokens/index.ts'),
        '@ob/tokens.css': path.resolve(
          __dirname,
          '../core/design-tokens/tokens.css',
        ),
      },
    },
  }
})
