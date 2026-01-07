import { expect, afterEach, vi } from 'vitest'

// Mock leaflet CSS to prevent import errors in JSDOM
vi.mock('leaflet/dist/leaflet.css', () => ({}))

import { cleanup } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'

// Extend Vitest's expect with jest-dom matchers
expect.extend(matchers)

function createStorageMock() {
  let store = new Map<string, string>()

  return {
    get length() {
      return store.size
    },
    clear() {
      store = new Map()
    },
    getItem(key: string) {
      return store.has(key) ? store.get(key)! : null
    },
    key(index: number) {
      return Array.from(store.keys())[index] ?? null
    },
    removeItem(key: string) {
      store.delete(key)
    },
    setItem(key: string, value: string) {
      store.set(String(key), String(value))
    },
  }
}

// Some tests/environment shims replace localStorage with a non-Storage object.
// Ensure we always have a spec-compatible surface for i18n and other modules.
Object.defineProperty(window, 'localStorage', {
  value: createStorageMock(),
  configurable: true,
})
Object.defineProperty(window, 'sessionStorage', {
  value: createStorageMock(),
  configurable: true,
})

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

// Recharts and other responsive components rely on ResizeObserver.
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

Object.defineProperty(window, 'ResizeObserver', {
  value: ResizeObserverMock,
  writable: true,
  configurable: true,
})

// Cleanup after each test
afterEach(() => {
  cleanup()
})
