import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { db } from '@/db'

/**
 * Hook to get property values without any filters applied.
 * This is useful for maintaining original boundaries in number filters.
 */
export function useOriginalPropertyValues(propertyId: string, query?: string) {
  return useQuery({
    queryKey: ['original-property-values', propertyId, query],
    queryFn: () => db.properties.values(propertyId, { query }), // No where or labels filters
    select: (data) => data.data,
    staleTime: 300000, // Cache for 5 minutes since original values don't change often
    placeholderData: keepPreviousData,
  })
}
