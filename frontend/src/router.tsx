/* eslint-disable react-refresh/only-export-components */
import type { AnchorHTMLAttributes, MouseEventHandler, ReactNode } from 'react'
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
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
  const routesRef = useRef(router.routes)
  routesRef.current = router.routes

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
    const exactMatch = routesRef.current.find((route) => route.path === path)
    if (exactMatch) {
      return exactMatch.element
    }

    return routesRef.current.find((route) => route.path === '/')?.element ?? null
  }, [path])

  const contextValue = useMemo<RouterContextValue>(() => ({ path, navigate }), [path, navigate])

  return <RouterContext.Provider value={contextValue}>{activeElement}</RouterContext.Provider>
}

interface LinkProps extends AnchorHTMLAttributes<HTMLAnchorElement> {
  to: string
  children: ReactNode
}

export function Link({ to, children, onClick, ...rest }: LinkProps) {
  const context = useContext(RouterContext)

  const handleClick: MouseEventHandler<HTMLAnchorElement> = useCallback(
    (event) => {
      if (onClick) {
        onClick(event)
      }

      if (event.defaultPrevented) {
        return
      }

      event.preventDefault()
      if (context) {
        context.navigate(to)
      }
    },
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
