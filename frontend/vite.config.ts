import path from 'node:path'

import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

function resolveManualChunk(id: string): string | undefined {
  if (id.includes('/node_modules/')) {
    if (id.includes('/@mui/icons-material/')) {
      return 'vendor-mui-icons'
    }
    if (id.includes('/@emotion/')) {
      return 'vendor-emotion'
    }
    if (
      id.includes('/@mui/material/') ||
      id.includes('/@mui/system/') ||
      id.includes('/@mui/utils/') ||
      id.includes('/@mui/lab/') ||
      id.includes('/@popperjs/')
    ) {
      return 'vendor-mui-core'
    }
    if (id.includes('/recharts/')) {
      return 'vendor-charts'
    }
    if (id.includes('/react-leaflet/') || id.includes('/leaflet/')) {
      return 'vendor-leaflet'
    }
    if (id.includes('/three/')) {
      return 'vendor-three'
    }
    if (
      id.includes('/react/') ||
      id.includes('/react-dom/') ||
      id.includes('/scheduler/')
    ) {
      return 'vendor-react'
    }
  }

  return undefined
}

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
      rollupOptions: {
        output: {
          manualChunks(id) {
            return resolveManualChunk(id)
          },
        },
      },
    },
  }
})
