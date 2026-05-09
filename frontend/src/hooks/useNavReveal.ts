import { useEffect, useRef, useState } from 'react'

interface UseNavRevealOptions {
  isPinned: boolean
}

interface UseNavRevealReturn {
  isRevealed: boolean
  reveal: () => void
  scheduleHide: () => void
  cancelHide: () => void
}

export function useNavReveal({
  isPinned,
}: UseNavRevealOptions): UseNavRevealReturn {
  const [isRevealed, setIsRevealed] = useState(false)
  const hideTimerRef = useRef<number | null>(null)

  const cancelHide = () => {
    if (typeof window === 'undefined') return
    if (hideTimerRef.current === null) return
    window.clearTimeout(hideTimerRef.current)
    hideTimerRef.current = null
  }

  const scheduleHide = () => {
    if (typeof window === 'undefined') return
    cancelHide()
    hideTimerRef.current = window.setTimeout(() => {
      setIsRevealed(false)
      hideTimerRef.current = null
    }, 350)
  }

  const reveal = () => {
    cancelHide()
    setIsRevealed(true)
  }

  useEffect(() => {
    // Reveal on any pin state change so the user sees the transition.
    setIsRevealed(true)
  }, [isPinned])

  return { isRevealed, reveal, scheduleHide, cancelHide }
}
