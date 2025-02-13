import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { db } from '@/db'
import { useSearchQuery } from '@/context/search-query-context'

export function usePropertyValues(propertyId: string, query?: string) {
  const { where = {}, labels } = useSearchQuery()

  return useQuery({
    queryKey: ['property-values', propertyId, where, labels, query],
    queryFn: () => db.properties.values(propertyId, { query }),
    select: (data) => data.data,
    staleTime: 30000,
    placeholderData: (previousData, previousQuery) => previousData,
  })
}
