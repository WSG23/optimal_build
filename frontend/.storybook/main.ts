import type { StorybookConfig } from '@storybook/react-vite'
import path from 'node:path'

const config: StorybookConfig = {
  stories: ['../src/**/*.stories.@(js|jsx|ts|tsx)'],
  addons: ['@storybook/addon-essentials', '@storybook/addon-a11y'],
  framework: {
    name: '@storybook/react-vite',
    options: {},
  },
  viteFinal: async (config) => {
    config.resolve = config.resolve || {}
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': path.resolve(__dirname, '../src'),
      '@ob/tokens': path.resolve(
        __dirname,
        '../../core/design-tokens/index.ts',
      ),
      '@ob/tokens.css': path.resolve(
        __dirname,
        '../../core/design-tokens/tokens.css',
      ),
    }
    return config
  },
}

export default config
