import { useSearchQuery } from '@/context/search-query-context'
import { getFromIndex } from '@/components/labels/utils'
import { labelVariants } from '@/components/labels/constants'
import { useCallback } from 'react'
import { useFetchQuery } from '@/hooks/use-fetch-query'

export function useLabels() {
  const { where, skip, limit } = useSearchQuery()

  const getLabelColor = useCallback((index: number) => {
    const array = Object.keys(labelVariants) as Array<string>
    return getFromIndex(array, index, 0)
  }, [])

  const { data, isLoading, error } = useFetchQuery<
    Array<{ label: string; value: number; color: string }>
  >({
    fetcher: async (signal) => {
      const res = await fetch(`/api/labels`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ where: where || {}, skip, limit }),
        signal,
      })
      if (!res.ok) throw new Error('Failed to load labels')
      const json = await res.json()
      return Object.entries(json.data as Record<string, number>).map(
        ([label, value], index) => ({
          label,
          value,
          color: getLabelColor(index),
        })
      )
    },
    deps: [where, skip, limit, getLabelColor],
    keepPreviousData: true,
  })

  return { data, isLoading, error }
}
