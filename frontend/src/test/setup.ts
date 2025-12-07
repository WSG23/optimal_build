import { expect, afterEach, vi } from 'vitest'

// Mock leaflet CSS to prevent import errors in JSDOM
vi.mock('leaflet/dist/leaflet.css', () => ({}))

import { cleanup } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'

// Extend Vitest's expect with jest-dom matchers
expect.extend(matchers)

// Mock matchMedia for JSDOM
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: unknown) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
})

// Cleanup after each test
afterEach(() => {
  cleanup()
})
