import { useSearchQuery } from '@/context/search-query-context'
import { useFetchQuery } from '@/hooks/use-fetch-query'
export function useCategoryItems(categoryId: string) {
  const {
    where = {},
    labels = ['ITEM'],
    skip,
    limit,
    orderBy,
  } = useSearchQuery()

  const { data, isLoading, error } = useFetchQuery<{
    items: any[]
    total?: number
    category: any
  }>({
    enabled: Boolean(categoryId),
    fetcher: async (signal) => {
      const res = await fetch(`/api/categories/${categoryId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ where, labels, skip, limit, orderBy }),
        signal,
      })
      if (!res.ok) throw new Error('Failed to load items')
      const json = await res.json()
      return json.data as { items: any[]; total?: number; category: any }
    },
    deps: [categoryId, where, labels, skip, limit, orderBy],
    keepPreviousData: true,
  })

  return { data, isLoading, error }
}
