import { useCallback, useEffect, useRef, useState } from 'react'

interface UseScrollAffordanceReturn {
  navRef: React.RefObject<HTMLDivElement | null>
  canScrollLeft: boolean
  canScrollRight: boolean
  scroll: (direction: 'left' | 'right') => void
  checkScroll: () => void
}

export function useScrollAffordance(): UseScrollAffordanceReturn {
  const navRef = useRef<HTMLDivElement | null>(null)
  const [canScrollLeft, setCanScrollLeft] = useState(false)
  const [canScrollRight, setCanScrollRight] = useState(false)

  const checkScroll = useCallback(() => {
    const node = navRef.current
    if (!node) return

    const { scrollLeft, scrollWidth, clientWidth } = node
    setCanScrollLeft(scrollLeft > 0)
    setCanScrollRight(scrollLeft < scrollWidth - clientWidth - 1)
  }, [])

  const scroll = useCallback((direction: 'left' | 'right') => {
    const node = navRef.current
    if (!node) return

    const scrollAmount = 240
    node.scrollBy({
      left: direction === 'left' ? -scrollAmount : scrollAmount,
      behavior: 'smooth',
    })
  }, [])

  useEffect(() => {
    checkScroll()
    if (typeof window === 'undefined') return
    window.addEventListener('resize', checkScroll)
    return () => window.removeEventListener('resize', checkScroll)
  }, [checkScroll])

  return { navRef, canScrollLeft, canScrollRight, scroll, checkScroll }
}
