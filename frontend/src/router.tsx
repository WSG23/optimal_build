/* eslint-disable react-refresh/only-export-components */
import type { AnchorHTMLAttributes, MouseEventHandler, ReactNode } from 'react'
import {
  createContext,
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
  navigate: (to: string) => void
}

const RouterContext = createContext<RouterContextValue | null>(null)

const getInitialPath = () => {
  if (typeof window === 'undefined') {
    return '/'
  }
  return window.location.pathname || '/'
}

export function createBrowserRouter(routes: RouteDefinition[]): RouterInstance {
  return { routes }
}

interface RouterProviderProps {
  router: RouterInstance
}

export function RouterProvider({ router }: RouterProviderProps) {
  const [path, setPath] = useState<string>(() => getInitialPath())
  const routes = useMemo(() => router?.routes ?? [], [router])

  useEffect(() => {
    if (typeof window === 'undefined') {
      return
    }

    const handlePopState = () => {
      setPath(window.location.pathname || '/')
    }

    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  const navigate = useCallback((to: string) => {
    if (typeof window !== 'undefined') {
      window.history.pushState({}, '', to)
    }
    setPath(to)
  }, [])

  const activeElement = useMemo(() => {
    const exactMatch = routes.find((route) => route.path === path)
    if (exactMatch) {
      return exactMatch.element
    }

    return routes.find((route) => route.path === '/')?.element ?? null
  }, [path, routes])

  const contextValue = useMemo<RouterContextValue>(
    () => ({ path, navigate }),
    [path, navigate],
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

    if (!shouldHandleLinkClick(event, event.currentTarget?.target)) {
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
  children: ReactNode
}

export function Link({ to, children, onClick, ...rest }: LinkProps) {
  const context = useContext(RouterContext)

  const handleClick = useMemo<MouseEventHandler<HTMLAnchorElement>>(
    () => createLinkClickHandler(context, to, onClick),
    [context, onClick, to],
  )

  return (
    <a href={to} onClick={handleClick} {...rest}>
      {children}
    </a>
  )
}

export function useRouterPath() {
  const context = useContext(RouterContext)
  if (!context) {
    return getInitialPath()
  }
  return context.path
}
