const metaEnv =
  typeof import.meta !== 'undefined' && import.meta
    ? (import.meta as ImportMeta).env
    : undefined

function getLocalStorageValue(key: string): string | undefined {
  if (typeof window === 'undefined') {
    return undefined
  }
  try {
    return window.localStorage.getItem(key) ?? undefined
  } catch {
    return undefined
  }
}

function pickIdentityValue(
  candidates: Array<string | undefined | null>,
  fallback: string | null = null,
): string | null {
  for (const candidate of candidates) {
    if (typeof candidate !== 'string') {
      continue
    }
    const trimmed = candidate.trim()
    if (trimmed.length > 0) {
      return trimmed
    }
  }
  return fallback
}

export function resolveDefaultRole(): string | null {
  return (
    pickIdentityValue(
      [metaEnv?.VITE_API_ROLE, getLocalStorageValue('app:api-role')],
      null,
    ) ?? null
  )
}

export function resolveDefaultUserEmail(): string | null {
  return (
    pickIdentityValue(
      [
        metaEnv?.VITE_API_USER_EMAIL,
        getLocalStorageValue('app:api-user-email'),
      ],
      null,
    ) ?? null
  )
}

export function resolveDefaultUserId(): string | null {
  return (
    pickIdentityValue(
      [metaEnv?.VITE_API_USER_ID, getLocalStorageValue('app:api-user-id')],
      null,
    ) ?? null
  )
}

export function applyIdentityHeaders<T extends Record<string, string>>(
  headers: T,
): T {
  const role = resolveDefaultRole()
  const email = resolveDefaultUserEmail()
  const userId = resolveDefaultUserId()
  const next: Record<string, string> = { ...headers }
  if (role && !next['X-Role']) {
    next['X-Role'] = role
  }
  if (email && !next['X-User-Email']) {
    next['X-User-Email'] = email
  }
  if (userId && !next['X-User-Id']) {
    next['X-User-Id'] = userId
  }
  return next as T
}

export function ensureIdentityHeaders(headers: Headers): void {
  const role = resolveDefaultRole()
  if (role && !headers.has('X-Role')) {
    headers.set('X-Role', role)
  }
  const email = resolveDefaultUserEmail()
  if (email && !headers.has('X-User-Email')) {
    headers.set('X-User-Email', email)
  }
  const userId = resolveDefaultUserId()
  if (userId && !headers.has('X-User-Id')) {
    headers.set('X-User-Id', userId)
  }
}
