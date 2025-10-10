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
