import { useRef, useEffect, useCallback } from 'react'

const FOCUSABLE_SELECTOR =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'

export interface UseFocusTrapOptions {
  isActive: boolean
  onClose: () => void
  initialFocusRef?: React.RefObject<HTMLElement>
}

function getFocusableElements(container: HTMLElement): HTMLElement[] {
  return Array.from(container.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR))
}

export default function useFocusTrap(options: UseFocusTrapOptions) {
  const { isActive, onClose, initialFocusRef } = options
  const internalRef = useRef<HTMLElement>(null)
  const previousFocusRef = useRef<HTMLElement | null>(null)

  const onCloseRef = useRef(onClose)
  onCloseRef.current = onClose

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.stopPropagation()
        onCloseRef.current()
        return
      }

      if (e.key !== 'Tab') return

      const container = internalRef.current
      if (!container) return

      const focusable = getFocusableElements(container)
      if (focusable.length === 0) return

      const first = focusable[0]
      const last = focusable[focusable.length - 1]

      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault()
          last.focus()
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault()
          first.focus()
        }
      }
    },
    [],
  )

  useEffect(() => {
    if (!isActive) {
      // Restore focus to the previously focused element
      if (previousFocusRef.current && typeof previousFocusRef.current.focus === 'function') {
        previousFocusRef.current.focus()
      }
      previousFocusRef.current = null
      return
    }

    // Save the currently focused element
    previousFocusRef.current = document.activeElement as HTMLElement | null

    const container = internalRef.current
    if (!container) return

    // Focus the first focusable element
    const focusable = getFocusableElements(container)
    if (focusable.length > 0) {
      if (initialFocusRef?.current) {
        initialFocusRef.current.focus()
      } else {
        focusable[0].focus()
      }
    }

    document.addEventListener('keydown', handleKeyDown)

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [isActive, handleKeyDown, initialFocusRef])

  return internalRef
}
