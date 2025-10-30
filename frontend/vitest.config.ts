import path from 'node:path'
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.test.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'src/**/*.test.{ts,tsx}',
        'src/**/__tests__/**',
        'src/test/**',
        '**/*.d.ts',
        '**/node_modules/**',
      ],
    },
  },
  resolve: {
    alias: {
      '@ob/tokens': path.resolve(__dirname, '../core/design-tokens/index.ts'),
      '@ob/tokens.css': path.resolve(
        __dirname,
        '../core/design-tokens/tokens.css',
      ),
    },
  },
})
