import { useFetchQuery } from '@/hooks/use-fetch-query'

export function useOriginalPropertyValues(propertyId: string, query?: string) {
  const { data, isLoading, error } = useFetchQuery<any>({
    enabled: Boolean(propertyId),
    fetcher: async (signal) => {
      const res = await fetch(`/api/properties/${propertyId}/values`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
        signal,
      })
      if (!res.ok) throw new Error('Failed to load original property values')
      const json = await res.json()
      return json.data
    },
    deps: [propertyId, query],
    keepPreviousData: true,
  })

  return { data, isLoading, error }
}
