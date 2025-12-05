/* eslint-disable react-refresh/only-export-components */
import type { AnchorHTMLAttributes, MouseEventHandler, ReactNode, Ref } from 'react'
import {
  createContext,
  forwardRef,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react'

interface RouteDefinition {
  path: string
  element: ReactNode
}

interface RouterInstance {
  routes: RouteDefinition[]
}

interface RouterContextValue {
  path: string
  search: string
  navigate: (to: string) => void
}

const RouterContext = createContext<RouterContextValue | null>(null)

const getInitialPath = () => {
  if (typeof window === 'undefined') {
    return '/'
  }
  return window.location.pathname || '/'
}

const getInitialSearch = () => {
  if (typeof window === 'undefined') {
    return ''
  }
  return window.location.search || ''
}

const resolvePath = (value: string): string => {
  if (typeof window === 'undefined') {
    if (value.includes('?')) {
      return value.split('?')[0] || '/'
    }
    if (value.includes('#')) {
      return value.split('#')[0] || '/'
    }
    return value || '/'
  }
  try {
    const url = new URL(value, window.location.origin)
    return url.pathname || '/'
  } catch {
    if (value.startsWith('?') || value.startsWith('#')) {
      return window.location.pathname || '/'
    }
    const [path] = value.split('?')
    return path.split('#')[0] || window.location.pathname || '/'
  }
}

const resolveSearch = (value: string): string => {
  if (typeof window === 'undefined') {
    return ''
  }
  try {
    const url = new URL(value, window.location.origin)
    return url.search || ''
  } catch {
    if (value.startsWith('?')) {
      return value
    }
    const [, searchPart] = value.split('?')
    return searchPart ? `?${searchPart.split('#')[0]}` : ''
  }
}

export function createBrowserRouter(routes: RouteDefinition[]): RouterInstance {
  return { routes }
}

interface RouterProviderProps {
  router: RouterInstance
}

export function RouterProvider({ router }: RouterProviderProps) {
  const [path, setPath] = useState<string>(() => getInitialPath())
  const [search, setSearch] = useState<string>(() => getInitialSearch())
  const routes = useMemo(() => router.routes, [router])

  useEffect(() => {
    if (typeof window === 'undefined') {
      return
    }

    const handlePopState = () => {
      setPath(window.location.pathname || '/')
      setSearch(window.location.search || '')
    }

    window.addEventListener('popstate', handlePopState)
    return () => {
      window.removeEventListener('popstate', handlePopState)
    }
  }, [])

  const navigate = useCallback((to: string) => {
    if (typeof window !== 'undefined') {
      window.history.pushState({}, '', to)
      setSearch(window.location.search || '')
      setPath(window.location.pathname || resolvePath(to))
      return
    }
    setSearch(resolveSearch(to))
    setPath(resolvePath(to))
  }, [])

  const activeElement = useMemo(() => {
    const exactMatch = routes.find((route) => route.path === path)
    if (exactMatch) {
      return exactMatch.element
    }

    // Check for parameterized routes (e.g., /agents/developers/:id/preview)
    const paramMatch = routes.find((route) => {
      const routeParts = route.path.split('/')
      const pathParts = path.split('/')

      if (routeParts.length !== pathParts.length) {
        return false
      }

      return routeParts.every((part, i) => {
        if (part.startsWith(':')) {
          return true // parameter match
        }
        return part === pathParts[i]
      })
    })

    if (paramMatch) {
      return paramMatch.element
    }

    return routes.find((route) => route.path === '/')?.element ?? null
  }, [path, routes])

  const contextValue = useMemo<RouterContextValue>(
    () => ({ path, search, navigate }),
    [navigate, path, search],
  )

  return (
    <RouterContext.Provider value={contextValue}>
      {activeElement}
    </RouterContext.Provider>
  )
}

type LinkMouseEvent = Parameters<MouseEventHandler<HTMLAnchorElement>>[0]

export function shouldHandleLinkClick(
  event: Pick<
    LinkMouseEvent,
    'button' | 'metaKey' | 'ctrlKey' | 'shiftKey' | 'altKey'
  >,
  target: string | null | undefined,
) {
  if (event.button !== 0) {
    return false
  }

  if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
    return false
  }

  if (target === '_blank') {
    return false
  }

  return true
}

export function createLinkClickHandler(
  context: RouterContextValue | null,
  to: string,
  onClick?: MouseEventHandler<HTMLAnchorElement>,
): MouseEventHandler<HTMLAnchorElement> {
  return (event) => {
    if (onClick) {
      onClick(event)
    }

    if (event.defaultPrevented) {
      return
    }

    if (!shouldHandleLinkClick(event, event.currentTarget.target)) {
      return
    }

    event.preventDefault()
    if (context) {
      context.navigate(to)
    }
  }
}

interface LinkProps extends AnchorHTMLAttributes<HTMLAnchorElement> {
  to: string
  children?: ReactNode
}

export const Link = forwardRef(function Link(
  { to, children, onClick, ...rest }: LinkProps,
  ref: Ref<HTMLAnchorElement>,
) {
  const context = useContext(RouterContext)

  const handleClick = useMemo<MouseEventHandler<HTMLAnchorElement>>(
    () => createLinkClickHandler(context, to, onClick),
    [context, onClick, to],
  )

  return (
    <a ref={ref} href={to} onClick={handleClick} {...rest}>
      {children}
    </a>
  )
})

export function useRouterPath() {
  const location = useRouterLocation()
  return location.path
}

export function useRouterController() {
  const context = useContext(RouterContext)
  if (!context) {
    const path = getInitialPath()
    const search = getInitialSearch()
    return {
      path,
      search,
      navigate: (to: string) => {
        if (typeof window !== 'undefined') {
          window.location.href = to
        }
      },
    }
  }
  return context
}

export function useRouterLocation() {
  const context = useContext(RouterContext)
  if (!context) {
    return {
      path: getInitialPath(),
      search: getInitialSearch(),
    }
  }
  return { path: context.path, search: context.search }
}
