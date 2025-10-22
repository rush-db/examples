import { useSearchQuery } from '@/context/search-query-context'
import { useFetchQuery } from '@/hooks/use-fetch-query'

export function useProperties() {
  const { where = {}, labels, skip, limit } = useSearchQuery()
  const { data, isLoading, error } = useFetchQuery<any[]>({
    fetcher: async (signal) => {
      const res = await fetch(`/api/properties`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ where, labels, skip, limit }),
        signal,
      })
      if (!res.ok) throw new Error('Failed to load properties')
      const json = await res.json()
      return json.data
    },
    deps: [where, labels, skip, limit],
    keepPreviousData: true,
  })

  return { data, isLoading, error }
}
