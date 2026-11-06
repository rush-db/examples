import { useSearchQuery } from '@/context/search-query-context'
import { useFetchQuery } from '@/hooks/use-fetch-query'

export function usePropertyValues(propertyId: string, query?: string) {
  const { where = {}, labels } = useSearchQuery()

  const { data, isLoading, error } = useFetchQuery<any>({
    enabled: Boolean(propertyId),
    fetcher: async (signal) => {
      const res = await fetch(`/api/properties/${propertyId}/values`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ where, labels, query }),
        signal,
      })
      if (!res.ok) throw new Error('Failed to load property values')
      const json = await res.json()
      return json.data
    },
    deps: [propertyId, where, labels, query],
    keepPreviousData: true,
  })

  return { data, isLoading, error }
}
