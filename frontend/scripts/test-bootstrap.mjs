import { JSDOM } from 'jsdom'

const bootstrapDom = new JSDOM('<!doctype html><html><body></body></html>', {
    url: 'http://localhost/',
})

Object.defineProperty(globalThis, 'window', {
    configurable: true,
    writable: true,
    value: bootstrapDom.window,
})

Object.defineProperty(globalThis, 'document', {
    configurable: true,
    writable: true,
    value: bootstrapDom.window.document,
})

Object.defineProperty(globalThis, 'navigator', {
    configurable: true,
    writable: true,
    value: bootstrapDom.window.navigator,
})

// Mock import.meta.env for Vite environment variables
const mockImportMeta = {
    env: {
        VITE_API_BASE_URL: 'http://localhost:9400',
        MODE: 'test',
        DEV: false,
        PROD: false,
        SSR: false,
    },
}

// Make import.meta available globally for tests
if (!globalThis.import) {
    globalThis.import = {}
}
globalThis.import.meta = mockImportMeta
