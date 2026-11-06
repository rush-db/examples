import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { db } from '@/db'
import { useSearchQuery } from '@/context/search-query-context'

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

  return useQuery({
    queryKey: ['property-values', propertyId, where, labels, query],
    queryFn: () => db.properties.values(propertyId, { where, labels, query }),
    select: (data) => data.data,
    staleTime: 30000,
    placeholderData: keepPreviousData,
    enabled, // This allows us to control when the query runs
  })
}
