const test = require('node:test')
const assert = require('node:assert/strict')
const path = require('node:path')

const { loadModule } = require('./helpers/loadModule.cjs')

const routerModule = loadModule(path.resolve(__dirname, '../src/router.tsx'))
const { createLinkClickHandler } = routerModule

function createEvent(overrides = {}) {
  let prevented = false
  const event = {
    button: 0,
    metaKey: false,
    ctrlKey: false,
    shiftKey: false,
    altKey: false,
    defaultPrevented: false,
    preventDefault() {
      prevented = true
      this.defaultPrevented = true
    },
    currentTarget: { target: '' },
    ...overrides,
  }

  return { event, wasPrevented: () => prevented }
}

test('modified clicks bypass router navigation', () => {
  const navigations = []
  const handler = createLinkClickHandler(
    {
      path: '/start',
      navigate: (to) => {
        navigations.push(to)
      },
    },
    '/destination',
  )

  for (const modifierKey of ['metaKey', 'ctrlKey']) {
    const { event, wasPrevented } = createEvent({ [modifierKey]: true })
    handler(event)
    assert.equal(wasPrevented(), false, `${modifierKey} should not call preventDefault`)
    assert.equal(
      navigations.length,
      0,
      `${modifierKey} should not trigger client-side navigation`,
    )
  }
})

test('plain left click uses router navigation', () => {
  const navigations = []
  const handler = createLinkClickHandler(
    {
      path: '/start',
      navigate: (to) => {
        navigations.push(to)
      },
    },
    '/destination',
  )

  const { event, wasPrevented } = createEvent()
  handler(event)

  assert.equal(wasPrevented(), true, 'preventDefault should be called for router navigation')
  assert.equal(navigations.length, 1)
  assert.equal(navigations[0], '/destination')
})
