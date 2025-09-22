const { buildSync } = require('esbuild')
const { createRequire } = require('module')
const path = require('path')
const vm = require('vm')

function loadModule(modulePath) {
  const absPath = path.resolve(modulePath)
  const result = buildSync({
    entryPoints: [absPath],
    bundle: true,
    platform: 'node',
    format: 'cjs',
    write: false,
    sourcemap: false,
    define: {
      'import.meta.env.VITE_API_BASE_URL': '""',
      'import.meta.env.VITE_FEASIBILITY_USE_MOCKS': '"false"',
    },
    external: ['react', 'react-dom', 'react/jsx-runtime'],
    loader: {
      '.ts': 'ts',
      '.tsx': 'tsx',
    },
  })

  const [{ text: code }] = result.outputFiles
  const module = { exports: {} }
  const req = createRequire(absPath)
  const context = {
    module,
    exports: module.exports,
    require: req,
    console,
    process,
    setTimeout,
    clearTimeout,
    setInterval,
    clearInterval,
    Buffer,
    fetch: (...args) => global.fetch(...args),
    URL,
    URLSearchParams,
    FormData: global.FormData,
    Array,
    Object,
  }
  vm.runInNewContext(code, context)
  return module.exports
}

module.exports = { loadModule }
