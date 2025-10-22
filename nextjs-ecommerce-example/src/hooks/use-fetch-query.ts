import { useCallback, useEffect, useRef, useState } from 'react'

type UseFetchQueryOptions<T> = {
  fetcher: (signal: AbortSignal) => Promise<T>
  deps: any[]
  enabled?: boolean
  keepPreviousData?: boolean
}

type UseFetchQueryResult<T> = {
  data: T | undefined
  isLoading: boolean
  error: Error | null
  refetch: () => Promise<void>
}

export function useFetchQuery<T>(
  options: UseFetchQueryOptions<T>
): UseFetchQueryResult<T> {
  const { fetcher, deps, enabled = true, keepPreviousData = true } = options

  const [data, setData] = useState<T | undefined>(undefined)
  const [isFetching, setIsFetching] = useState<boolean>(false)
  const [error, setError] = useState<Error | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const load = useCallback(async () => {
    if (!enabled) return

    // Do not clear data when keeping previous data to prevent UI flicker
    if (!keepPreviousData) setData(undefined)
    setIsFetching(true)
    setError(null)

    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    let isActive = true
    try {
      const result = await fetcher(controller.signal)
      if (isActive) setData(result)
    } catch (e: any) {
      if (e?.name !== 'AbortError') {
        if (isActive) setError(e)
      }
    } finally {
      if (isActive) setIsFetching(false)
    }

    return () => {
      isActive = false
      controller.abort()
    }
  }, [enabled, fetcher, keepPreviousData])

  useEffect(() => {
    // Trigger load on mount and whenever deps change
    load()
    return () => {
      abortRef.current?.abort()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  const refetch = useCallback(async () => {
    await load()
  }, [load])

  const isLoading = isFetching && data === undefined
  return { data, isLoading, error, refetch }
}
