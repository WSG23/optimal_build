import path from 'node:path'
import { defineConfig } from 'vitest/config'

export default defineConfig(async () => {
  const react = (await import('@vitejs/plugin-react')).default

  return {
    plugins: [react()],
    test: {
      globals: true,
      environment: 'jsdom',
      pool: 'threads',
      minThreads: 1,
      maxThreads: 2,
      setupFiles: ['./src/test/setup.ts'],
      include: [
        'src/app/pages/capture/components/DeveloperResults.test.tsx',
        'src/app/pages/capture/hooks/__tests__/useUnifiedCapture.test.tsx',
      ],
      coverage: {
        provider: 'v8',
        reporter: ['text', 'html', 'lcov'],
        include: [
          'src/app/pages/capture/components/DeveloperResults.tsx',
          'src/app/pages/capture/hooks/useUnifiedCapture.ts',
        ],
        exclude: [
          'src/**/__tests__/**',
          'src/**/*.{test,spec}.{ts,tsx}',
          'src/test/**',
        ],
        thresholds: {
          perFile: true,
          lines: 75,
          statements: 75,
          functions: 60,
          branches: 55,
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
