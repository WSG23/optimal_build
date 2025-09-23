function toSnakeCaseKey(key) {
  return key
    .replace(/([A-Z])/g, '_$1')
    .replace(/[-\s]+/g, '_')
    .toLowerCase()
}

function toCamelCaseKey(key) {
  return key.replace(/[_-](\w)/g, (_, char) => char.toUpperCase())
}

function snakeCase(value) {
  if (Array.isArray(value)) {
    return value.map((item) => snakeCase(item))
  }
  if (value && typeof value === 'object' && !(value instanceof Date)) {
    const result = {}
    for (const [key, nested] of Object.entries(value)) {
      result[toSnakeCaseKey(key)] = snakeCase(nested)
    }
    return result
  }
  return value
}

function camelCase(value) {
  if (Array.isArray(value)) {
    return value.map((item) => camelCase(item))
  }
  if (value && typeof value === 'object' && !(value instanceof Date)) {
    const result = {}
    for (const [key, nested] of Object.entries(value)) {
      result[toCamelCaseKey(key)] = camelCase(nested)
    }
    return result
  }
  return value
}

function normaliseBaseUrl(baseUrl, fallback = '/api/v1/') {
  if (!baseUrl) {
    return fallback
  }
  return baseUrl
}

function joinUrl(baseUrl, path) {
  const normalised = normaliseBaseUrl(baseUrl)
  if (/^https?:/i.test(normalised)) {
    return new URL(path, normalised).toString()
  }
  if (normalised.endsWith('/')) {
    return `${normalised}${path}`
  }
  return `${normalised}/${path}`
}

module.exports = {
  snakeCase,
  camelCase,
  joinUrl,
  normaliseBaseUrl,
}
