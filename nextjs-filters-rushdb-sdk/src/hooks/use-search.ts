import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { useSearchQuery } from '@/context/search-query-context'
import {
  DBRecordsArrayInstance,
  DBRecordInstance,
} from '@rushdb/javascript-sdk'

type SearchSettings = {
  vectorDimension: number
}

export function useSearch(
  searchText: string = '',
  searchSettings?: SearchSettings
) {
  const { where, labels, skip, limit } = useSearchQuery()

  // Check if BACKEND_URL is defined - safely handle both server and client side
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL
  const isSearchEnabled =
    typeof backendUrl === 'string' && backendUrl.length > 0

  return useQuery({
    queryKey: [
      'search',
      searchText,
      where,
      labels,
      skip,
      limit,
      searchSettings?.vectorDimension,
    ],
    queryFn: async () => {
      // Return empty result if BACKEND_URL is not defined or if there's no search text
      if (!isSearchEnabled || !searchText.trim()) {
        return { data: [], total: 0 }
      }

      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL
      const url = new URL(`${backendUrl}/search`)

      const response = await fetch(url.toString(), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: searchText,
          where,
          labels,
          skip,
          limit,
          vector_dimension: searchSettings?.vectorDimension || 384,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to fetch search results')
      }

      return await response.json()
    },
    select: (data) =>
      new DBRecordsArrayInstance(
        data.data.map((record: any) => new DBRecordInstance(record)),
        data.total
      ),
    staleTime: 120000,
    placeholderData: keepPreviousData,
    enabled: isSearchEnabled && !!searchText.trim(),
  })
}
