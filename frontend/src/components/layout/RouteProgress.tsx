import { useEffect, useState } from 'react'

/** Track the completion flash element to prevent orphan nodes on rapid navigation. */
let activeFlashEl: HTMLDivElement | null = null

/** Check reduced motion preference at module level for the unmount flash (no hook access). */
function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined') return false
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

/**
 * Thin 2px progress bar fixed at the top of the viewport.
 * Used as a Suspense fallback during lazy route loading.
 *
 * On mount: animates width from 0 -> ~85% in staggered jumps.
 * On unmount: injects a brief 100%-width bar that fades out,
 * giving the visual "complete" effect.
 *
 * Respects `prefers-reduced-motion: reduce` by disabling
 * transitions and the completion flash animation.
 */
export function RouteProgress() {
  const [width, setWidth] = useState(0)

  useEffect(() => {
    const reducedMotion = prefersReducedMotion()

    if (reducedMotion) {
      // Skip intermediate steps; jump straight to final width
      setWidth(85)
    } else {
      const t1 = requestAnimationFrame(() => setWidth(15))
      const t2 = setTimeout(() => setWidth(45), 150)
      const t3 = setTimeout(() => setWidth(72), 400)
      const t4 = setTimeout(() => setWidth(85), 900)

      return () => {
        cancelAnimationFrame(t1)
        clearTimeout(t2)
        clearTimeout(t3)
        clearTimeout(t4)

        completionFlash(false)
      }
    }

    return () => {
      completionFlash(prefersReducedMotion())
    }
  }, [])

  const reducedMotion = prefersReducedMotion()

  return (
    <div
      aria-hidden="true"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        height: 2,
        width: `${width}%`,
        background: 'var(--ob-color-brand-primary)',
        zIndex: 'var(--ob-z-fixed, 1030)' as unknown as number,
        transition: reducedMotion
          ? 'none'
          : 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        pointerEvents: 'none',
      }}
    />
  )
}

/** Inject the completion flash bar on unmount. */
function completionFlash(reducedMotion: boolean) {
  // Clean up any previous flash element
  if (activeFlashEl) {
    activeFlashEl.remove()
    activeFlashEl = null
  }

  if (reducedMotion) {
    // No animation: briefly show 100% bar then remove immediately
    const el = document.createElement('div')
    el.setAttribute('aria-hidden', 'true')
    Object.assign(el.style, {
      position: 'fixed',
      top: '0',
      left: '0',
      height: '2px',
      width: '100%',
      background: 'var(--ob-color-brand-primary)',
      zIndex: 'var(--ob-z-fixed, 1030)',
      pointerEvents: 'none',
      opacity: '1',
      transition: 'none',
    })
    document.body.appendChild(el)
    activeFlashEl = el
    // Remove after a single frame so the user sees the bar at 100%
    requestAnimationFrame(() => {
      if (activeFlashEl === el) {
        el.remove()
        activeFlashEl = null
      }
    })
    return
  }

  // Completion flash: inject a 100%-width bar that fades out
  const el = document.createElement('div')
  el.setAttribute('aria-hidden', 'true')
  Object.assign(el.style, {
    position: 'fixed',
    top: '0',
    left: '0',
    height: '2px',
    width: '100%',
    background: 'var(--ob-color-brand-primary)',
    zIndex: 'var(--ob-z-fixed, 1030)',
    pointerEvents: 'none',
    opacity: '1',
    transition: 'opacity 0.3s ease-out',
  })
  document.body.appendChild(el)
  activeFlashEl = el
  requestAnimationFrame(() => {
    el.style.opacity = '0'
  })
  setTimeout(() => {
    if (activeFlashEl === el) {
      el.remove()
      activeFlashEl = null
    }
  }, 350)
}
