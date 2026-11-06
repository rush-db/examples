import { useSearchQuery } from '@/context/search-query-context'
import {
  keepPreviousData,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'
import { db } from '@/db'

export function useProperties() {
  const { where = {}, labels, skip, limit } = useSearchQuery()
  return useQuery({
    queryKey: ['properties', where, labels, skip, limit],
    queryFn: () => db.properties.find({ where, labels, skip, limit }),
    select: (data) => {
      return data.data
    },
    placeholderData: keepPreviousData,
  })
}
