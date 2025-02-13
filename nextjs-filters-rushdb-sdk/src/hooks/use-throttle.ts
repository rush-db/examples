import { useCallback, useRef } from 'react'

export const useThrottle = (
  callback: (...args: any[]) => void,
  delayMs: number = 100
) => {
  const lastCall = useRef(0)

  return useCallback(
    (...args: any[]) => {
      const now = Date.now()
      if (now - lastCall.current >= delayMs) {
        lastCall.current = now
        callback(...args)
      }
    },
    [callback, delayMs]
  )
}
