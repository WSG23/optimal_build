import path from 'node:path'

import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { compression } from 'vite-plugin-compression2'

// NOTE: This file used to define a `resolveManualChunk` that put
// @emotion, @mui/material, recharts, @mui/icons-material, leaflet,
// three, and react/react-dom into separate vendor-* chunks. Every one
// of those splits produced a runtime TDZ in the production build
// ("Cannot access 'X' before initialization") because the chunked
// packages have cyclic transitive deps (hoist-non-react-statics,
// @babel/runtime helpers, victory-vendor/d3-*, etc.) that Rollup
// places in other chunks. The resulting cross-chunk init order is
// undefined and breaks every E2E test on the prod build with a blank
// page. Vite/Rollup's default chunking handles these cycles correctly,
// so we no longer pass `output.manualChunks`.

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
    plugins: [
      react(),
      compression({ algorithm: 'gzip', threshold: 1024 }),
      compression({ algorithm: 'brotliCompress', threshold: 1024 }),
    ],
    server: {
      port: Number.isFinite(serverPort) ? serverPort : 3000,
      strictPort: false, // Auto-pick next available port if taken
      host,
      fs: {
        allow: [path.resolve(__dirname, '..')],
      },
      proxy: {
        '/api': {
          target: proxyTarget,
          changeOrigin: true,
          ws: true,
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
    build: {
      target: 'esnext',
      minify: 'esbuild',
      sourcemap: false,
      chunkSizeWarningLimit: 1000,
    },
  }
})
