import { useSearchQuery } from '@/context/search-query-context'
import { useFetchQuery } from '@/hooks/use-fetch-query'

/**
 * Lazy loading version of usePropertyValues hook.
 * Only fetches data when enabled is true, useful for large datasets
 * that should only be loaded when dropdowns/popovers are opened.
 *
 * Use this for:
 * - String filters (can have thousands of options)
 * - DateTime filters (date ranges)
 *
 * Don't use this for:
 * - Boolean filters (limited options, need immediate UI)
 * - Number filters (need immediate data to determine single value vs range UI)
 */
export function usePropertyValuesLazy(
  propertyId: string,
  enabled: boolean = true,
  query?: string
) {
  const { where = {}, labels } = useSearchQuery()

  const { data, isLoading, error, refetch } = useFetchQuery<any>({
    enabled: enabled && Boolean(propertyId),
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
    deps: [enabled, propertyId, where, labels, query],
    keepPreviousData: true,
  })

  return { data, isLoading, error, refetch }
}
