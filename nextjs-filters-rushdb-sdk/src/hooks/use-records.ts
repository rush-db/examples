import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { db } from '@/db'
import { useSearchQuery } from '@/context/search-query-context'

export function useRecords() {
  const { where, labels, skip, limit } = useSearchQuery()

  return useQuery({
    queryKey: ['records', where, labels, skip, limit],
    queryFn: () => db.records.find({ where, labels, skip, limit }),
    staleTime: 120000,
    placeholderData: keepPreviousData,
  })
}
