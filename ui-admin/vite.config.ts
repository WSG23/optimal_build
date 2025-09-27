import path from 'node:path';

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    fs: {
      allow: [path.resolve(__dirname, '..')]
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  resolve: {
    alias: {
      '@ob/tokens': path.resolve(__dirname, '../core/design-tokens/index.ts'),
      '@ob/tokens.css': path.resolve(__dirname, '../core/design-tokens/tokens.css')
    }
  }
});
